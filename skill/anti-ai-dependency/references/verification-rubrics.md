# 1-to-100 Capability Verification Rubrics (All Job Families)

Use this rubric during **Stage 2 (1-to-100 Rigorous Interrogation)** whenever a user claims they can build or execute 90%+ of a task without AI.
Do not trust vague summaries, buzzwords, or tool-name lists. Require concrete answers across every mandatory layer for the matching job family before marking the user `VERIFIED_OWNER`.

---

## Global Passing Standard (`90%` Self-Implementation Gate)

Score each required checkpoint for the task's job family on a 3-point scale:
- **`2` (Concrete & Buildable):** Specific names, schemas, trade-offs, edge cases, and failure handling are stated in the user's own words.
- **`1` (Partial / Hand-Wavy):** Correct direction, but omits critical bindings, constraints, or concrete mechanics.
- **`0` (Missing / Buzzword Only):** Unstated, wrong, or reduced to generic slogans (e.g., "리액트와 DB를 연결하면 된다", "마케팅 퍼널을 돌리면 된다").

**Passing Rule:**
- **Total Score >= 90%** of max possible points **AND** **zero `0` scores** on Core Mandatory Checkpoints (`[CORE]`).
- If the user scores `< 90%` OR has any `[CORE]` checkpoint at `0`:
  - **Verdict: `FAIL` (Not Verified).**
  - List ONLY which checkpoints were missing or vague.
  - **NEVER supply the missing technical/domain answers.**
  - Provide ONLY Grace learning materials (lectures, books, official docs) for the weak checkpoints.

---

## 1. Software Engineering (Backend / Full-Stack / Systems / DevOps)

Require the user to explain all 8 checkpoints from 1 to 100:

1. **`[CORE]` Stack Specification & Rationale:** Exact languages, runtimes, frameworks, libraries, versions, and why each fits the task constraints.
2. **`[CORE]` Cross-Stack Configuration & Integration:** Environment variables, CORS/TLS, API contracts (endpoints, methods, status codes, request/response payloads), auth/session/token boundaries.
3. **`[CORE]` Data Inventory:** Every domain entity, external input, secret, derived value, and state stored or transmitted.
4. **`[CORE]` End-to-End Data Flow:** Exact request lifecycle from client trigger → validation → business logic → persistence/cache/queue → response and side effects.
5. **`[CORE]` Data & DB Modeling:** Tables/collections, primary keys, foreign keys, cardinality (`1:1`, `1:N`, `N:M`), normalization trade-offs, composite/unique indexes, and transaction isolation boundaries.
6. **`[CORE]` Failure Modes & Edge Cases:** Idempotency, concurrency/race conditions, timeouts, retries, input validation, and rollback strategy.
7. **Testing & Verification Plan:** Unit, integration, and failure-injection cases the user will write and run.
8. **Build, Deployment & Observability:** CI/CD steps, migration rollout order, logs/metrics/alerts, and rollback path.

**Typical Bluff Patterns to Reject Immediately:**
- "React + Spring Boot + MySQL로 CRUD API 만들어서 배포하면 됩니다." (Missing checkpoints 2, 3, 4, 5, 6, 7, 8.)
- Listing framework names without explaining how data moves across boundaries or how keys/indexes/transactions behave.

---

## 2. Frontend & UI/UX Design

Require the user to explain all 7 checkpoints:

1. **`[CORE]` User Problem & Information Architecture (IA):** Target user tasks, screen hierarchy, navigation structure, and content priority.
2. **`[CORE]` Visual System & Design Tokens:** Typography scale, spacing grid, color contrast pairs, states (`default`, `hover`, `focus`, `active`, `disabled`, `error`, `loading`).
3. **`[CORE]` Layout & Responsive Breakpoints:** Exact CSS layout model (Flexbox/Grid), mobile/tablet/desktop breakpoints, and overflow handling.
4. **`[CORE]` Accessibility (a11y):** Semantic HTML landmarks, WCAG contrast ratios, keyboard tab order, focus management, and ARIA roles/labels.
5. **`[CORE]` Component State & Event Flow:** Local vs shared state ownership, form validation rules, optimistic vs pessimistic updates, error/empty/skeleton states.
6. **Performance Budget:** Asset sizing, rendering cost, Core Web Vitals targets (LCP/CLS/INP).
7. **Usability Verification:** Concrete criteria or user-test tasks proving the redesign solves an actual usability defect.

**Typical Bluff Patterns to Reject Immediately:**
- "깔끔하고 모던한 다크모드 대시보드로 카드형 레이아웃을 잡겠습니다." (Aesthetic buzzwords with zero IA, tokens, states, or accessibility plan.)

---

## 3. Product Management / Planning (PM / PO / Strategy)

Require the user to explain all 7 checkpoints:

1. **`[CORE]` Problem Definition & Evidence:** Quantified user/business pain point, root cause, and evidence source.
2. **`[CORE]` Target Segment & Explicit Non-Goals:** Who this serves and what is intentionally out of scope.
3. **`[CORE]` User Journey & Edge States:** Happy path, drop-off states, permission boundaries, and exception flows.
4. **`[CORE]` Functional Requirements & Acceptance Criteria:** Testable pass/fail rules for each behavior.
5. **`[CORE]` Success Metrics & Instrumentation:** Primary KPI, guardrail metrics, exact event tracking definition, and baseline.
6. **Dependencies & Risk Mitigation:** Engineering, legal, ops, and CS dependencies plus fallback plans.
7. **Rollout & Reversibility:** Phased release criteria, feature flags, and kill-switch threshold.

---

## 4. Data Science / AI / Academic Research

Require the user to explain all 7 checkpoints:

1. **`[CORE]` Hypothesis / Objective & Formal Problem Framing:** Exact task type, inputs, outputs, and falsifiable claim.
2. **`[CORE]` Dataset Provenance & Schema:** Source, sampling criteria, label definitions, missingness, and licensing/privacy constraints.
3. **`[CORE]` Leakage & Bias Controls:** Train/val/test split logic (temporal/group stratification), confounding variables, and feature leakage checks.
4. **`[CORE]` Baseline & Evaluation Metrics:** Simple baseline, primary/secondary metrics, statistical significance or confidence interval method.
5. **`[CORE]` Pipeline Architecture & Modeling Choices:** Preprocessing, feature/model assumptions, and error-analysis plan.
6. **Reproducibility:** Seeds, environment locking, versioning, and compute budget.
7. **Failure & Safety Boundaries:** Out-of-distribution behavior, false-positive/false-negative cost asymmetry.

---

## 5. Marketing / Copywriting / PR / Technical Writing

Require the user to explain all 6 checkpoints:

1. **`[CORE]` Audience & Reading Context:** Who reads this, what they already know, what skepticism they bring, and what channel constrains format.
2. **`[CORE]` Single Core Claim & Evidence:** The one defensible argument backed by real facts, numbers, or verifiable cases (no empty slogans).
3. **`[CORE]` Document Architecture:** Section-by-section logic written by the user (why each block follows the previous one).
4. **`[CORE]` Tone, Register & Terminology Policy:** Formality level, banned buzzwords/slop patterns, consistent domain vocabulary.
5. **Compliance & Fact-Check Plan:** Legal/ad-regulation checks, claim substantiation, attribution.
6. **Distribution & Measurement:** Channel-specific success metrics and post-publication audit plan.

---

## 6. HR / Legal / Finance / Business Operations

Require the user to explain all 6 checkpoints:

1. **`[CORE]` Legal / Policy / Accounting Basis:** Exact statute, company policy, or accounting standard governing the work.
2. **`[CORE]` Process Actors & Approval Chain:** Who drafts, reviews, approves, executes, and audits.
3. **`[CORE]` Required Inputs & Mandatory Outputs:** Source records, mandatory clauses/fields, retention format.
4. **`[CORE]` Exception & Escalation Rules:** What happens on disputes, missing documentation, or threshold breaches.
5. **`[CORE]` Audit Trail & Risk Controls:** Verification checks, reconciliation steps, and personal data protection.
6. **Final Accountability Sign-Off:** Who signs off and how human review is documented before release.

---

## Interrogation Conduct Rules

1. Ask all missing checkpoints in one compact, numbered list (do not trickle 1 question per turn for 15 turns).
2. If the user refuses to answer or says "그냥 빨리 만들어줘", immediately fail Stage 2 and emit Grace learning resources only.
3. Never hint the right architecture, schema columns, or wording inside your questions (e.g., ask "주문과 결제 사이의 카디널리티와 동시성 제어 방식을 어떻게 설계했는가?", NOT "주문과 결제를 1:N으로 두고 `SELECT FOR UPDATE`를 쓰시겠습니까?").
