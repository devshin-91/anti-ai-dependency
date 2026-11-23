#!/usr/bin/env python3
"""Deterministic policy leakage auditor, 1-to-100 gate scorer, and anti-slop bridge.

Zero external dependencies (Python 3 standard library only).
Integrates with sibling `anti-slop-editor/scripts/slop_engine.py` for deterministic
AI-slop and invisible Unicode scanning on assistant responses.

Subcommands:
  score-gate      Compute deterministic 1-to-100 verification pass/fail (>=90%, zero core 0s).
  audit-response  Check an assistant reply for code/config/command leaks, prose/rewrite/template
                  leaks, Grace reference presence, and anti-slop cleanliness.
"""

from __future__ import annotations

import argparse
import codecs
import json
import locale
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

# Ensure UTF-8 I/O on Windows consoles/pipes (including stdin)
for _stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Universal Unicode Input Decoding (UTF-8/BOM, UTF-16/32, Legacy Fallbacks)
# ---------------------------------------------------------------------------

def decode_unicode_bytes(raw: bytes, *, strip_bom: bool = False) -> str:
    """Decode raw bytes across any Unicode encoding or legacy locale fallback."""
    text: str | None = None

    # 1. Explicit Unicode BOMs (check 4-byte UTF-32 before 2-byte UTF-16)
    try:
        if len(raw) >= 4 and len(raw) % 4 == 0 and raw.startswith((codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
            text = raw.decode("utf-32")
        elif len(raw) >= 2 and len(raw) % 2 == 0 and raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
            text = raw.decode("utf-16")
        elif raw.startswith(codecs.BOM_UTF8):
            text = raw.decode("utf-8-sig" if strip_bom else "utf-8")
    except UnicodeDecodeError:
        text = None

    # 2. BOM-less UTF-32 / UTF-16 heuristic when NUL bytes are present
    if text is None and b"\x00" in raw:
        if len(raw) >= 4 and len(raw) % 4 == 0:
            n4 = len(raw) // 4
            # Valid Unicode codepoints are <= U+10FFFF: top byte is always 0x00, second byte <= 0x10
            if raw[3::4].count(0) == n4 and all(b <= 0x10 for b in raw[2::4]):
                try:
                    text = raw.decode("utf-32-le")
                except UnicodeDecodeError:
                    pass
            elif raw[0::4].count(0) == n4 and all(b <= 0x10 for b in raw[1::4]):
                try:
                    text = raw.decode("utf-32-be")
                except UnicodeDecodeError:
                    pass
        if text is None and len(raw) >= 4 and len(raw) % 2 == 0:
            even_nulls = raw[0::2].count(0)
            odd_nulls = raw[1::2].count(0)
            threshold = max(2, len(raw) // 8)
            if odd_nulls >= threshold and odd_nulls > even_nulls:
                try:
                    text = raw.decode("utf-16-le")
                except UnicodeDecodeError:
                    pass
            elif even_nulls >= threshold and even_nulls > odd_nulls:
                try:
                    text = raw.decode("utf-16-be")
                except UnicodeDecodeError:
                    pass

    # 3. Strict UTF-8 (standard universal path)
    if text is None:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            pass

    # 4. Locale & common CJK / Western legacy fallbacks (CP949, Shift-JIS, GB18030, CP1252)
    if text is None:
        pref = locale.getpreferredencoding(False)
        candidates: list[str] = []
        for enc in (pref, "cp949", "euc-kr", "gb18030", "shift_jis", "cp1252"):
            if enc and enc.lower() not in {c.lower() for c in candidates}:
                candidates.append(enc)
        for enc in candidates:
            try:
                text = raw.decode(enc)
                break
            except (LookupError, UnicodeDecodeError):
                continue

    # 5. Guaranteed non-crashing fallback
    if text is None:
        text = raw.decode("utf-8", errors="replace")

    if strip_bom and text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")

    # Normalize CRLF / CR to LF (equivalent to Python universal newlines)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_unicode_input(path_arg: str | Path, *, strip_bom: bool = False) -> str:
    """Read a file path or '-' (stdin) with universal Unicode encoding detection."""
    if str(path_arg) == "-":
        buf = getattr(sys.stdin, "buffer", None)
        if buf is not None:
            return decode_unicode_bytes(buf.read(), strip_bom=strip_bom)
        text = sys.stdin.read()
        if strip_bom and text.startswith("\ufeff"):
            text = text.lstrip("\ufeff")
        return text.replace("\r\n", "\n").replace("\r", "\n")
    return decode_unicode_bytes(Path(path_arg).read_bytes(), strip_bom=strip_bom)


# ---------------------------------------------------------------------------
# Deterministic Leakage Pattern Registries
# ---------------------------------------------------------------------------

# Fenced code blocks (` ```lang ... ``` `)
FENCED_BLOCK_RE = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)

# Permitted read-only diagnostic command (anti-slop scan pointer only, 1 line)
ALLOWED_SLOP_SCAN_RE = re.compile(
    r"^\s*python\s+[^\n]*slop_engine\.py\s+scan\b[^\n]*$",
    re.IGNORECASE,
)

# Unfenced code / SQL / markup / CLI recipe line patterns
CODE_LINE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("python_def_or_import", re.compile(r"^\s*(def|class|async\s+def|from\s+\w+\s+import|import\s+\w+)\b")),
    ("js_ts_decl", re.compile(r"^\s*(export\s+)?(const|let|var|function|interface|type)\s+\w+\s*[=:(<]")),
    ("java_c_decl", re.compile(r"^\s*(public|private|protected)\s+(static\s+)?(class|interface|void|\w+)\s+\w+")),
    ("sql_statement", re.compile(r"^\s*(CREATE\s+TABLE|ALTER\s+TABLE|SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM)\b", re.IGNORECASE)),
    ("html_jsx_tag", re.compile(r"^\s*<(div|section|main|header|form|button|input|table|nav|script|style)\b[^>]*>", re.IGNORECASE)),
    ("css_rule", re.compile(r"^\s*[.#]?[a-zA-Z_-][a-zA-Z0-9_-]*\s*\{\s*(display|grid|flex|color|background|margin|padding)\s*:")),
    ("dockerfile_or_yaml", re.compile(r"^\s*(FROM\s+\w+:\w+|RUN\s+\w+|COPY\s+\S+\s+\S+|apiVersion:|kind:\s+(Deployment|Service|Pod)|stages:|jobs:)")),
    ("shell_recipe", re.compile(r"^\s*(git\s+(init|add|commit|push|remote|branch|checkout)|docker\s+(build|run|compose)|kubectl\s+apply|npm\s+(install|run)|pip\s+install)\b")),
    ("excel_formula", re.compile(r"=\s*(NPV|IRR|SUM|XLOOKUP|VLOOKUP|INDEX|MATCH|IFERROR)\s*\(", re.IGNORECASE)),
]

# Prose / rewrite / template / copywriting / outline delivery patterns
PROSE_REWRITE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("korean_rewrite_header", re.compile(r"(^|\n)\s*(#{1,4}\s*|\*\*|\[)?\s*(수정본|교정본|교정안|수정안|개선안|초안|완성본|추천\s*문구|대안\s*문장|예시\s*문구|예시\s*문장|복사해서\s*사용)\s*(\*\*|\])?\s*[:：]", re.IGNORECASE)),
    ("english_rewrite_header", re.compile(r"(^|\n)\s*(#{1,4}\s*|\*\*)?\s*(Rewritten|Polished\s+version|Suggested\s+rewrite|Draft|Copy-paste|Here\s+is\s+(a|the)\s+(draft|rewrite|template|README|copy))\b", re.IGNORECASE)),
    ("korean_before_after_rewrite", re.compile(r"(수정\s*전|원문)\s*[:：].{1,300}(수정\s*후|개선\s*후|교정\s*후)\s*[:：]", re.DOTALL)),
    ("korean_multi_option_copy", re.compile(r"(옵션|버전|안)\s*[1A]\s*[:：].{1,300}(옵션|버전|안)\s*[2B]\s*[:：]", re.DOTALL)),
    ("korean_letter_draft", re.compile(r"(^|\n)\s*(안녕하십니까|안녕하세요,?\s*[^\n]{0,20}입니다|수신\s*[:：]|발신\s*[:：]|제목\s*[:：]\s*\[)")),
    ("contract_clause_draft", re.compile(r"(^|\n)\s*제\s*\d+\s*조\s*\([^)]+\)")),
    ("fill_in_template_blank", re.compile(r"\[(회사명|서비스명|담당자명|날짜|지표|수치|금액)\s*(입력)?\]")),
]

# Chatbot sycophancy & Korean AI-slop tells strictly banned in refusals
BANNED_SLOP_TONE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("chatbot_closing", re.compile(r"(도움이\s*되셨길\s*바랍니다|궁금한\s*점이\s*있으시면\s*언제든|응원합니다|충분히\s*해내실\s*수\s*있|화이팅)")),
    ("chatbot_praise", re.compile(r"(좋은\s*질문입니다|훌륭한\s*(접근|설계|도전)입니다|멋진\s*아이디어)")),
    ("false_binary_cliche", re.compile(r"(단순히\s+.{1,30}\s*(이|가)\s*아니라|에\s*그치지\s*않고)")),
    ("p1_calque_metaphor", re.compile(r"(라는\s*렌즈로|세\s*개의\s*기둥|성장의\s*여정|잠재력을\s*잠금\s*해제|결론적으로)")),
]

# Verified learning/reference cues (URLs, canonical books/docs/standards)
REFERENCE_CUE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"https?://[a-zA-Z0-9._-]+"),
    re.compile(r"\b(MDN|WCAG|WAI-ARIA|OWASP|RFC\s*\d+|PostgreSQL|MySQL|React|Spring|Python|Docker|Kubernetes|GitHub\s*Docs|Pro\s*Git|Google\s+SRE|Google\s+Technical\s+Writing|ASD-STE100|K-IFRS|APA|IEEE|NN/g|Nielsen\s+Norman|Material\s+Design|Human\s+Interface\s+Guidelines|re:Work|OPM|NCS|DART|Damodaran|Excel)\b", re.IGNORECASE),
    re.compile(r"(Designing\s+Data-Intensive\s+Applications|The\s+Elements\s+of\s+Style|On\s+Writing\s+Well|Don't\s+Make\s+Me\s+Think|The\s+Design\s+of\s+Everyday\s+Things|Refactoring\s+UI|Inspired|Continuous\s+Discovery\s+Habits|Escaping\s+the\s+Build\s+Trap|Lean\s+Analytics|Designing\s+Machine\s+Learning\s+Systems|Elements\s+of\s+Statistical\s+Learning|Everybody\s+Writes|Ogilvy\s+on\s+Advertising|Breakthrough\s+Advertising|A\s+Philosophy\s+of\s+Software\s+Design|Investment\s+Valuation|Work\s+Rules|Hire\s+with\s+Your\s+Head)", re.IGNORECASE),
    re.compile(r"(국립국어원|우리글\s*바로\s*쓰기|글쓰기\s*특강|강원국의\s*글쓰기|국가법령정보센터|개인정보보호위원회|고용노동부|공정거래위원회|한국회계기준원|국가직무능력표준|전자공시시스템|공식\s*문서|교재|강의|참고\s*자료|표준\s*가이드|slop_engine\.py|lang-ko\.md|skills\.md)"),
]

# Invisible Unicode chars checked independently even if slop_engine is unavailable
INVISIBLE_CHARS = ("\u202f", "\u200b", "\u200c", "\u200d", "\ufeff")


# ---------------------------------------------------------------------------
# 1. Deterministic 1-to-100 Gate Scorer
# ---------------------------------------------------------------------------

def score_gate(payload: dict[str, Any], threshold_pct: float = 90.0) -> dict[str, Any]:
    """Compute exact 1-to-100 readiness percentage and PASS/FAIL verdict."""
    checkpoints = payload.get("checkpoints", [])
    if not isinstance(checkpoints, list) or not checkpoints:
        raise ValueError("Payload must contain a non-empty 'checkpoints' list.")

    total_earned = 0
    total_max = 0
    core_zeros: list[str] = []
    weak_items: list[str] = []

    for cp in checkpoints:
        cp_id = str(cp.get("id", "unnamed"))
        is_core = bool(cp.get("core", False))
        score = cp.get("score")
        if score not in (0, 1, 2):
            raise ValueError(f"Checkpoint '{cp_id}' score must be 0, 1, or 2 (got {score!r}).")
        total_earned += score
        total_max += 2
        if is_core and score == 0:
            core_zeros.append(cp_id)
        if score < 2:
            weak_items.append(cp_id)

    pct = round((total_earned / total_max) * 100.0, 2) if total_max else 0.0
    passed = (pct >= threshold_pct) and (len(core_zeros) == 0)

    return {
        "domain": payload.get("domain", "general"),
        "earned_points": total_earned,
        "max_points": total_max,
        "readiness_pct": pct,
        "threshold_pct": threshold_pct,
        "core_zero_blockers": core_zeros,
        "weak_or_missing_checkpoints": weak_items,
        "verdict": "PASS" if passed else "FAIL",
        "owner_status": "VERIFIED_OWNER" if passed else "UNVERIFIED_REFUSE",
    }


# ---------------------------------------------------------------------------
# 2. Anti-Slop Engine Integration
# ---------------------------------------------------------------------------

def locate_slop_engine(explicit_path: str | None = None) -> Path | None:
    """Find sibling anti-slop-editor/scripts/slop_engine.py if installed."""
    if explicit_path:
        p = Path(explicit_path)
        return p if p.is_file() else None

    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "anti-slop-editor" / "scripts" / "slop_engine.py",
        Path.home() / ".gemini" / "config" / "skills" / "anti-slop-editor" / "scripts" / "slop_engine.py",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def run_slop_scan(text: str, slop_engine_path: Path | None, genre: str = "tech") -> dict[str, Any]:
    """Run anti-slop-editor's deterministic slop_engine.py scan via subprocess."""
    invisible_count = sum(text.count(ch) for ch in INVISIBLE_CHARS)
    if not slop_engine_path:
        return {
            "available": False,
            "invisible_unicode_count": invisible_count,
            "route_hint": "light" if invisible_count == 0 else "standard",
            "hit_count": 0,
            "families": [],
            "error": "slop_engine.py not found",
        }

    try:
        child_env = os.environ.copy()
        child_env["PYTHONUTF8"] = "1"
        child_env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(slop_engine_path), "scan", "-", "--genre", genre, "--json"],
            input=text.encode("utf-8", errors="replace"),
            capture_output=True,
            timeout=15,
            check=False,
            env=child_env,
        )
        stdout_text = proc.stdout.decode("utf-8", errors="replace")
        stderr_text = proc.stderr.decode("utf-8", errors="replace")
        if proc.returncode != 0 or not stdout_text.strip():
            return {
                "available": False,
                "invisible_unicode_count": invisible_count,
                "route_hint": "unknown",
                "hit_count": 0,
                "families": [],
                "error": stderr_text.strip() or f"exit {proc.returncode}",
            }
        data = json.loads(stdout_text)
        inv = data.get("invisible_unicode", {})
        inv_total = inv.get("total", invisible_count) if isinstance(inv, dict) else invisible_count
        hits = data.get("hits", [])
        families = sorted({h.get("family", "") for h in hits if isinstance(h, dict) and h.get("family")})
        return {
            "available": True,
            "language": data.get("language", "unknown"),
            "route_hint": data.get("route_hint", "light"),
            "invisible_unicode_count": inv_total,
            "hit_count": len(hits),
            "families": families,
            "score": data.get("total_weight", 0),
        }
    except Exception as exc:
        return {
            "available": False,
            "invisible_unicode_count": invisible_count,
            "route_hint": "unknown",
            "hit_count": 0,
            "families": [],
            "error": str(exc),
        }


# ---------------------------------------------------------------------------
# 3. Deterministic Policy Response Auditor
# ---------------------------------------------------------------------------

def audit_response(
    text: str,
    slop_engine_path: Path | None = None,
    genre: str = "tech",
) -> dict[str, Any]:
    """Audit an assistant response for code/prose leakage, resources, and AI slop."""
    code_leaks: list[dict[str, Any]] = []
    prose_leaks: list[dict[str, Any]] = []
    slop_tone_hits: list[dict[str, Any]] = []

    # 1. Inspect fenced code blocks
    stripped_for_line_scan = text
    for match in FENCED_BLOCK_RE.finditer(text):
        lang = (match.group(1) or "").strip().lower()
        body = match.group(2).strip()
        lines = [ln for ln in body.splitlines() if ln.strip()]
        # Permit strictly a single-line read-only slop_engine.py scan command
        if len(lines) == 1 and ALLOWED_SLOP_SCAN_RE.match(lines[0]):
            continue
        code_leaks.append({
            "type": "fenced_code_block",
            "lang": lang or "plain",
            "line_count": len(lines),
            "snippet": body[:140],
        })
    stripped_for_line_scan = FENCED_BLOCK_RE.sub("", text)

    # 2. Inspect unfenced lines for code/SQL/HTML/CSS/shell/formula leakage
    unfenced_hits: list[dict[str, Any]] = []
    for idx, line in enumerate(stripped_for_line_scan.splitlines(), start=1):
        clean_ln = line.strip()
        if not clean_ln:
            continue
        if ALLOWED_SLOP_SCAN_RE.match(clean_ln):
            continue
        for rule_name, pattern in CODE_LINE_PATTERNS:
            if pattern.search(line):
                unfenced_hits.append({
                    "type": f"unfenced_{rule_name}",
                    "line": idx,
                    "snippet": clean_ln[:140],
                })
                break
    # Single shell/SQL/code line in unfenced text is already suspicious; flag all concrete code lines
    code_leaks.extend(unfenced_hits)

    # 3. Inspect prose / rewrite / template / copywriting delivery leaks
    for rule_name, pattern in PROSE_REWRITE_PATTERNS:
        m = pattern.search(text)
        if m:
            prose_leaks.append({
                "type": rule_name,
                "snippet": m.group(0).strip()[:140],
            })

    # 4. Inspect reference/Grace resource cues
    reference_matches: list[str] = []
    for cue_re in REFERENCE_CUE_PATTERNS:
        for m in cue_re.finditer(text):
            token = m.group(0).strip()
            if token not in reference_matches:
                reference_matches.append(token)

    # 5. Inspect banned sycophancy / Korean slop tells + slop_engine.py scan
    for rule_name, pattern in BANNED_SLOP_TONE_PATTERNS:
        m = pattern.search(text)
        if m:
            slop_tone_hits.append({
                "type": rule_name,
                "snippet": m.group(0).strip()[:100],
            })

    slop_scan = run_slop_scan(text, slop_engine_path, genre=genre)
    c2_pass = len(code_leaks) == 0
    c3_pass = len(prose_leaks) == 0
    c7_clean = (
        len(slop_tone_hits) == 0
        and slop_scan.get("invisible_unicode_count", 0) == 0
        and slop_scan.get("route_hint") != "heavy"
    )

    return {
        "c2_zero_code_leak": c2_pass,
        "c3_zero_prose_leak": c3_pass,
        "c7_anti_slop_clean": c7_clean,
        "has_reference_resources": len(reference_matches) > 0,
        "reference_count": len(reference_matches),
        "reference_samples": reference_matches[:10],
        "code_leaks": code_leaks,
        "prose_leaks": prose_leaks,
        "slop_tone_hits": slop_tone_hits,
        "slop_engine_scan": slop_scan,
        "char_length": len(text),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Anti-AI-Dependency deterministic auditor & gate scorer.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_gate = sub.add_parser("score-gate", help="Score 1-to-100 capability checkpoints from JSON.")
    p_gate.add_argument("input_json", help="Path to checkpoint JSON file (or '-' for stdin).")
    p_gate.add_argument("--threshold", type=float, default=90.0, help="Passing percentage (default 90.0).")

    p_audit = sub.add_parser("audit-response", help="Audit an assistant response for policy leakage and AI slop.")
    p_audit.add_argument("input_file", nargs="?", default="-", help="Path to response text file (or '-' for stdin).")
    p_audit.add_argument("--genre", default="tech", help="Genre for slop_engine.py scan (default: tech).")
    p_audit.add_argument("--slop-engine", default=None, help="Optional explicit path to slop_engine.py.")

    args = parser.parse_args()

    if args.cmd == "score-gate":
        raw = read_unicode_input(args.input_json, strip_bom=True)
        result = score_gate(json.loads(raw), threshold_pct=args.threshold)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "audit-response":
        raw = read_unicode_input(args.input_file, strip_bom=False)
        slop_path = locate_slop_engine(args.slop_engine)
        result = audit_response(raw, slop_engine_path=slop_path, genre=args.genre)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
