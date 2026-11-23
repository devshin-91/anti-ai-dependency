# Verified Grace & Self-Study Reference Catalog

Use ONLY verified, canonical documentation, textbooks, standards, and courses from this catalog (or other primary official docs you verify) when delivering **Grace (Stage 1/2 Fail)** or **Reference Curation (Stage 3)**.
Never invent URLs, course names, or book titles. Never replace these links with ready-to-paste code, templates, or rewritten user sentences.

---

## 1. Software Engineering (Backend / Databases / Systems / Security)

- **System & Data Architecture:** Martin Kleppmann, *Designing Data-Intensive Applications* (O'Reilly)
- **Software Design:** John Ousterhout, *A Philosophy of Software Design*; Martin Fowler, *Refactoring* (Addison-Wesley)
- **HTTP & Web Standards:** MDN Web Docs (`https://developer.mozilla.org/`), RFC 9110 HTTP Semantics (`https://www.rfc-editor.org/rfc/rfc9110`)
- **Databases:** PostgreSQL Official Docs (`https://www.postgresql.org/docs/`), MySQL Reference Manual (`https://dev.mysql.com/doc/`)
- **Languages & Frameworks:**
  - Python Official Docs (`https://docs.python.org/3/`)
  - Spring Framework Reference (`https://docs.spring.io/spring-framework/reference/`)
  - Node.js Official Docs (`https://nodejs.org/docs/`)
  - Go Official Documentation (`https://go.dev/doc/`)
- **Security:** OWASP Cheat Sheet Series (`https://cheatsheetseries.owasp.org/`), OWASP Top 10 (`https://owasp.org/www-project-top-ten/`)
- **Operations & Cloud:** Google SRE Book (`https://sre.google/sre-book/table-of-contents/`), The Twelve-Factor App (`https://12factor.net/`), Docker Docs (`https://docs.docker.com/`), Kubernetes Docs (`https://kubernetes.io/docs/`)

## 2. Frontend & UI/UX Design

- **Web Platform Core:** MDN HTML/CSS/JS Guides (`https://developer.mozilla.org/en-US/docs/Learn`)
- **Frameworks & Types:** React Official Docs (`https://react.dev/`), TypeScript Handbook (`https://www.typescriptlang.org/docs/handbook/`)
- **Accessibility Standards:** W3C WCAG 2.2 (`https://www.w3.org/TR/WCAG22/`), WAI-ARIA Authoring Practices Guide (`https://www.w3.org/WAI/ARIA/apg/`)
- **UI/UX Heuristics & Design Systems:**
  - Nielsen Norman Group: 10 Usability Heuristics (`https://www.nngroup.com/articles/ten-usability-heuristics/`)
  - Material Design 3 Guidelines (`https://m3.material.io/`)
  - Apple Human Interface Guidelines (`https://developer.apple.com/design/human-interface-guidelines/`)
- **Design Books:** Don Norman, *The Design of Everyday Things*; Steve Krug, *Don't Make Me Think*; Adam Wathan & Steve Schoger, *Refactoring UI*

## 3. Product Management & Strategy (PM / PO)

- Marty Cagan, *Inspired: How to Create Tech Products Customers Love*
- Teresa Torres, *Continuous Discovery Habits*
- Melissa Perri, *Escaping the Build Trap*
- Alistair Croll & Benjamin Yoskovitz, *Lean Analytics*

## 4. Data Science, ML & Academic Research

- **Foundations:** Trevor Hastie, Robert Tibshirani, Jerome Friedman, *The Elements of Statistical Learning*; Stanford CS229 / CS231n Course Notes
- **ML Systems:** Chip Huyen, *Designing Machine Learning Systems* (O'Reilly)
- **Tool Documentation:** scikit-learn User Guide (`https://scikit-learn.org/stable/user_guide.html`), PyTorch Docs (`https://pytorch.org/docs/stable/`), pandas Docs (`https://pandas.pydata.org/docs/`)
- **Academic Writing & Citation:** APA Style (`https://apastyle.apa.org/`), IEEE Author Center (`https://journals.ieeeauthorcenter.ieee.org/`)

## 5. Writing, Expressions, Technical Docs & Anti-Slop Self-Audit

When a user asks to fix phrasing, polish prose, remove AI tone, or draft documents, refuse rewriting and point them to these self-study guides:

- **Korean Grammar & Natural Prose:**
  - 국립국어원 한국어 어문 규범 (`https://korean.go.kr/`)
  - 이오덕, *우리글 바로 쓰기* (한길사)
  - 유시민, *유시민의 글쓰기 특강* (생각의길)
  - 강원국, *강원국의 글쓰기* (메디치미디어)
- **English & Technical Writing:**
  - Google Technical Writing Courses (`https://developers.google.com/tech-writing`)
  - ASD-STE100 Simplified Technical English (`https://asd-ste100.org/`)
  - William Strunk Jr. & E. B. White, *The Elements of Style*
  - William Zinsser, *On Writing Well*
- **Anti-Slop Diagnostic Reference (Read-Only Study; NEVER Invoke AI Rewrite Modes):**
  - Local pattern guides inside `anti-slop-editor`: `references/lang-ko.md`, `references/lang-en.md`, `references/architecture-and-genres.md`
  - Deterministic local scanner (prints flagged pattern signals only; human edits the file manually):
    `python "<skills_dir>/anti-slop-editor/scripts/slop_engine.py" scan <your_file> --genre <genre>`

## 6. Marketing, Copywriting & PR

- Ann Handley, *Everybody Writes*
- David Ogilvy, *Ogilvy on Advertising*
- Eugene Schwartz, *Breakthrough Advertising*
- 공정거래위원회 표시·광고 법령 안내 (`https://www.ftc.go.kr/`)

## 7. HR, Recruiting & Structured Interviewing

- **Structured Interviews & Assessment:**
  - Google re:Work: Structured Interviewing Guide (`https://rework.withgoogle.com/guides/hiring-use-structured-interviewing/steps/introduction/`)
  - U.S. OPM: Structured Interviews Guide (`https://www.opm.gov/policy-data-oversight/assessment-and-selection/structured-interviews/`)
- **Job Analysis & Competency Standards:**
  - 국가직무능력표준(NCS) 직무기술서·능력단위 포털 (`https://www.ncs.go.kr/`)
- **Recruiting & People Ops Books:**
  - Laszlo Bock, *Work Rules!* (Twelve)
  - Lou Adler, *Hire with Your Head* (Wiley)
- **Hiring Compliance (Only when labor/hiring law applies):** 고용노동부 (`https://www.moel.go.kr/`)

## 8. Legal, Compliance & Privacy

- 대한민국 법령 원문: 국가법령정보센터 (`https://www.law.go.kr/`)
- 개인정보 규정: 개인정보보호위원회 (`https://www.pipc.go.kr/`)
- 노동법·근로계약 기준: 고용노동부 (`https://www.moel.go.kr/`)
- 생활법령 안내: 법제처 찾기 쉬운 생활법령정보 (`https://easylaw.go.kr/`)

## 9. Finance, Accounting & Valuation

- **Valuation & Financial Modeling:**
  - Aswath Damodaran, *Investment Valuation* (Wiley) & NYU Stern Damodaran Online (`https://pages.stern.nyu.edu/~adamodar/`)
  - McKinsey & Company (Tim Koller et al.), *Valuation: Measuring and Managing the Value of Companies* (Wiley)
- **Spreadsheet Financial Functions:**
  - Microsoft Support: Excel Financial Functions Reference (`https://support.microsoft.com/en-us/office/financial-functions-reference-5658d81e-6035-4f24-89c1-fbf124c2b1d8`)
- **Accounting Standards & Disclosures:**
  - 한국회계기준원 K-IFRS (`https://www.kasb.or.kr/`)
  - 금융감독원 전자공시시스템 DART (`https://dart.fss.or.kr/`)

## 10. Git, GitHub & Antigravity Skill Authoring

- **Git:** Scott Chacon & Ben Straub, *Pro Git* (`https://git-scm.com/book/ko/v2`, `https://git-scm.com/book/en/v2`)
- **GitHub:** GitHub Official Docs (`https://docs.github.com/`): Repositories, SSH Keys, Pull Requests, GitHub Flavored Markdown (`https://github.github.com/gfm/`)
- **Antigravity Skills & Customizations:**
  - Antigravity Official Docs (`https://antigravity.google/docs`)
  - Local built-in spec: `agy-customizations/docs/skills.md` and `agy-customizations/SKILL.md`
