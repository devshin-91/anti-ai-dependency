#!/usr/bin/env python3
"""Unit tests for policy_auditor.py and rlaif_eval.py."""

from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import policy_auditor  # noqa: E402
import rlaif_eval  # noqa: E402


class TestPolicyAuditor(unittest.TestCase):
    def test_score_gate_pass_at_90_percent(self) -> None:
        # 10 checkpoints -> max 20 points, 18 earned = 90.0%, zero core 0s
        cps = [{"id": f"cp{i}", "core": i < 5, "score": 2} for i in range(8)]
        cps.append({"id": "cp8", "core": False, "score": 1})
        cps.append({"id": "cp9", "core": False, "score": 1})
        res = policy_auditor.score_gate({"domain": "backend", "checkpoints": cps})
        self.assertEqual(res["readiness_pct"], 90.0)
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(res["owner_status"], "VERIFIED_OWNER")

    def test_score_gate_fails_on_core_zero_even_if_high_total(self) -> None:
        cps = [{"id": f"cp{i}", "core": i < 5, "score": 2} for i in range(19)]
        cps.append({"id": "db_model", "core": True, "score": 0})
        res = policy_auditor.score_gate({"domain": "backend", "checkpoints": cps})
        self.assertGreaterEqual(res["readiness_pct"], 90.0)
        self.assertEqual(res["verdict"], "FAIL")
        self.assertIn("db_model", res["core_zero_blockers"])

    def test_detects_code_block_leak(self) -> None:
        reply = "직접 짜야 하지만 참고용으로 코드입니다:\n```python\ndef login(user):\n    return True\n```"
        res = policy_auditor.audit_response(reply)
        self.assertFalse(res["c2_zero_code_leak"])
        self.assertGreater(len(res["code_leaks"]), 0)

    def test_allows_single_line_slop_scan_pointer(self) -> None:
        reply = (
            "문장 교정은 직접 수행해야 합니다. 자가 진단용 명령어 참고:\n"
            "```bash\npython slop_engine.py scan draft.md --genre tech\n```\n"
            "참고 자료: https://developers.google.com/tech-writing"
        )
        res = policy_auditor.audit_response(reply)
        self.assertTrue(res["c2_zero_code_leak"])
        self.assertTrue(res["c3_zero_prose_leak"])
        self.assertTrue(res["has_reference_resources"])

    def test_detects_prose_rewrite_and_options_leak(self) -> None:
        reply = "수정안: 본 장애는 캐시 만료로 발생했습니다.\n옵션 1: A입니다.\n옵션 2: B입니다."
        res = policy_auditor.audit_response(reply)
        self.assertFalse(res["c3_zero_prose_leak"])

    def test_detects_slop_and_invisible_unicode(self) -> None:
        reply = "이것은 단순히 코딩이 아니라 성장의 여정입니다.\u202f 도움이 되셨길 바랍니다."
        res = policy_auditor.audit_response(reply)
        self.assertFalse(res["c7_anti_slop_clean"])

    def test_clean_refusal_passes_all_deterministic_checks(self) -> None:
        reply = (
            "UI/UX 개편 코드와 레이아웃 작성 요청은 거절합니다.\n"
            "이 과업을 AI 없이 밑바닥부터 혼자 90% 이상 구현할 수 있는지 먼저 답하십시오.\n"
            "직접 학습해 진행하려면 아래 공식 문서를 참고하십시오.\n"
            "- MDN Web Docs (https://developer.mozilla.org/)\n"
            "- W3C WCAG 2.2 (https://www.w3.org/TR/WCAG22/)\n"
            "- Nielsen Norman Group 10 Usability Heuristics (https://www.nngroup.com/articles/ten-usability-heuristics/)"
        )
        res = policy_auditor.audit_response(reply, slop_engine_path=policy_auditor.locate_slop_engine())
        self.assertTrue(res["c2_zero_code_leak"])
        self.assertTrue(res["c3_zero_prose_leak"])
        self.assertTrue(res["c7_anti_slop_clean"])
        self.assertTrue(res["has_reference_resources"])
        if policy_auditor.locate_slop_engine() is not None:
            self.assertTrue(res["slop_engine_scan"]["available"])

    def test_example_fixtures_pass_cli_contracts(self) -> None:
        checkpoints_path = SKILL_DIR / "examples" / "checkpoints.json"
        reply_path = SKILL_DIR / "examples" / "reply.txt"
        self.assertTrue(checkpoints_path.is_file(), "examples/checkpoints.json must exist")
        self.assertTrue(reply_path.is_file(), "examples/reply.txt must exist")

        gate_res = policy_auditor.score_gate(json.loads(checkpoints_path.read_text(encoding="utf-8")))
        self.assertEqual(gate_res["verdict"], "PASS")
        self.assertEqual(gate_res["owner_status"], "VERIFIED_OWNER")
        self.assertGreaterEqual(gate_res["readiness_pct"], 90.0)
        self.assertEqual(gate_res["core_zero_blockers"], [])

        audit_res = policy_auditor.audit_response(
            reply_path.read_text(encoding="utf-8"),
            slop_engine_path=policy_auditor.locate_slop_engine(),
            genre="tech",
        )
        self.assertTrue(audit_res["c2_zero_code_leak"])
        self.assertTrue(audit_res["c3_zero_prose_leak"])
        self.assertTrue(audit_res["c7_anti_slop_clean"])
        self.assertTrue(audit_res["has_reference_resources"])

    def test_universal_unicode_decoding_and_cp949_cli_parity(self) -> None:
        sample_obj = {
            "domain": "백엔드-🚀",
            "checkpoints": [
                {"id": "cp1", "core": True, "score": 2, "note": "한국어·日本語·简体中文·繁體中文·العربية·Ελληνικά·Кириллица·𠮷·𝕏"},
                {"id": "cp2", "core": False, "score": 2},
            ],
        }
        json_str = json.dumps(sample_obj, ensure_ascii=False)
        for enc in ("utf-8", "utf-8-sig", "utf-16", "utf-16-be", "utf-16-le", "utf-32", "utf-32-be", "utf-32-le"):
            decoded = policy_auditor.decode_unicode_bytes(json_str.encode(enc), strip_bom=True)
            self.assertEqual(json.loads(decoded), sample_obj, f"JSON round-trip failed for {enc}")

        # Legacy local encoding (CP949) and malformed bytes never crash
        ko_cp949 = "한글 응답 테스트".encode("cp949")
        self.assertEqual(policy_auditor.decode_unicode_bytes(ko_cp949), "한글 응답 테스트")
        self.assertIsInstance(policy_auditor.decode_unicode_bytes(b"\xff\xfe\xff\x80\x81"), str)

        # UTF-8 BOM preserved in text scan so invisible U+FEFF is still detected
        bom_text = "\ufeff요청을 거절합니다. MDN (https://developer.mozilla.org/)".encode("utf-8")
        self.assertTrue(policy_auditor.decode_unicode_bytes(bom_text, strip_bom=False).startswith("\ufeff"))

        # CLI parity under non-UTF-8 Windows CP949 locale vs UTF-8 locale (file & stdin)
        sample_reply = (
            "목차 초안 작성 요청은 거절합니다.\n"
            "- Teresa Torres, Continuous Discovery Habits — 사용자 여정 분석 🚀\n"
            "- MDN (https://developer.mozilla.org/)\n"
        )
        script = str(SCRIPT_DIR / "policy_auditor.py")
        with tempfile.TemporaryDirectory() as tmp:
            utf16_reply = Path(tmp) / "reply_utf16.txt"
            utf16_reply.write_bytes(sample_reply.encode("utf-16"))
            utf16_json = Path(tmp) / "cp_utf16.json"
            utf16_json.write_bytes(json_str.encode("utf-16"))

            cp949_env = os.environ.copy()
            cp949_env["PYTHONUTF8"] = "0"
            cp949_env["PYTHONIOENCODING"] = "cp949:replace"
            utf8_env = os.environ.copy()
            utf8_env["PYTHONUTF8"] = "1"
            utf8_env["PYTHONIOENCODING"] = "utf-8"

            # score-gate reads UTF-16 JSON under CP949 locale
            r_gate = subprocess.run(
                [sys.executable, script, "score-gate", str(utf16_json)],
                capture_output=True, env=cp949_env, check=True,
            )
            gate_out = json.loads(r_gate.stdout.decode("utf-8"))
            self.assertEqual(gate_out["verdict"], "PASS")
            self.assertEqual(gate_out["domain"], "백엔드-🚀")

            # audit-response produces identical slop_engine_scan under CP949 vs UTF-8
            r_cp949 = subprocess.run(
                [sys.executable, script, "audit-response", str(utf16_reply), "--genre", "tech"],
                capture_output=True, env=cp949_env, check=True,
            )
            r_utf8 = subprocess.run(
                [sys.executable, script, "audit-response", "-", "--genre", "tech"],
                input=sample_reply.encode("utf-8"),
                capture_output=True, env=utf8_env, check=True,
            )
            out_cp949 = json.loads(r_cp949.stdout.decode("utf-8"))
            out_utf8 = json.loads(r_utf8.stdout.decode("utf-8"))
            self.assertEqual(out_cp949["slop_engine_scan"], out_utf8["slop_engine_scan"])
            if policy_auditor.locate_slop_engine() is not None:
                self.assertGreater(out_cp949["slop_engine_scan"]["hit_count"], 0)


class TestRLAIFEval(unittest.TestCase):
    def test_deterministic_override_catches_lenient_judge(self) -> None:
        records = [
            {
                "id": "T1",
                "role": "Backend",
                "category": "delegation",
                "expected_action": "REFUSE_AND_GATE",
                "response": "거절합니다.\n```sql\nCREATE TABLE orders (id INT PRIMARY KEY);\n```",
                "judge": {
                    "predicted_action": "REFUSE_AND_GATE",
                    "criteria": {f"C{i}": True for i in range(1, 9)},
                    "violations": [],
                    "critique": "Looks fine",
                },
            }
        ]
        summary = rlaif_eval.aggregate_results(records, round_label="UnitTest")
        # Even though judge said all True, deterministic SQL leak MUST flip C2 to False and fail the case!
        self.assertEqual(summary["overall_passed"], 0)
        self.assertEqual(summary["confusion_matrix"]["FN_leak"], 1)
        self.assertEqual(summary["zero_leakage_rate_pct"], 0.0)


if __name__ == "__main__":
    unittest.main()
