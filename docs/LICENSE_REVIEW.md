# License review (prepared for Rehan's approval — not applied)

## Current state

| Where | License |
|---|---|
| `main` (`cb517fa`, Mohammad) | Apache License 2.0 |
| `feature/13b-release-candidate` (this branch, unchanged since the repo's `e46f176` initial commit) | MIT License, Copyright (c) 2026 Mohammad. S |
| Official SDC submission template | Apache License 2.0 |

## Recommendation (not applied — requires your approval)

**Apache 2.0**, matching both `main`'s own explicit, deliberate change and the official template. This
is a recommendation only; the `LICENSE` file in this branch has **not** been modified.

## Compatibility check against actual dependencies

MIT → Apache 2.0 is a **permissive-to-permissive** relicensing of the team's own original code; it does
not remove any right a recipient already had under MIT, and it does not require any dependency to
also be Apache-licensed. Every third-party dependency declared in
`submission/SDC2026_CodeBlack_TechDeclaration.pdf` §2.2 is itself permissively licensed and compatible
with either MIT or Apache 2.0 as the *project's own* license:

| Category | Licenses present | Compatible with relicensing the project to Apache 2.0? |
|---|---|---|
| Backend (FastAPI, Pydantic, SQLAlchemy, httpx, pypdf, python-multipart, python-dotenv) | MIT, BSD-3-Clause, Apache-2.0 | Yes |
| Frontend (React, react-router, Vite, Tailwind, radix-ui, clsx, tailwind-merge, lenis) | MIT | Yes |
| Frontend (TypeScript, class-variance-authority) | Apache-2.0 | Yes (already Apache-2.0) |
| Frontend (lucide-react) | ISC | Yes (ISC is MIT-equivalent in substance) |
| RunPod worker (runpod SDK, sentence-transformers, transformers) | MIT, Apache-2.0 | Yes |
| RunPod worker (torch) | Apache-2.0 **AND** Apache-2.0-with-LLVM-exception **AND** BSD-2-Clause **AND** BSD-3-Clause **AND** BSL-1.0 **AND** MIT (multi-component license per PyTorch's own metadata) | Yes — every component listed is itself permissive |
| Frontend animation (GSAP, @gsap/react) | **GSAP Standard No-Charge License** — free to use, but **not an OSI-approved open-source license** | **Needs your attention** — see below |
| Dev-only tooling (pytest, oxlint, @types/*) | MIT | Yes (not shipped to end users anyway) |

## The one real flag: GSAP

GSAP's "Standard No-Charge License" is **not** a standard open-source license (MIT/Apache/BSD) — it's
a free-to-use proprietary license from Webflow/GreenSock with its own terms. This does not block
relicensing the *project's own* code to Apache 2.0 (GSAP stays under its own license regardless, the
same as it already does under the current MIT setup), but:
- The README's third-party attribution section should name GSAP's license by name rather than
  imply it's open source.
- If the submission or judging criteria require every dependency to be OSI-approved open source,
  this is the one dependency that does not qualify — flagging for your awareness, not blocking.

## Data licensing (separate from code licensing)

- O*NET occupational data: **CC BY 4.0**, attribution required — this applies to the *data*, independent
  of whatever license the code carries. See the README's O*NET Attribution section.
- UCI ML Repository and World Bank datasets (linked only, never copied into the app): CC BY 4.0.
- Learning resource links: each provider's own terms; not redistributed.

## What I did NOT do

I did not modify `LICENSE`, `main`, or any dependency. This document is a review only, prepared per
your instruction in Phase 10 of the submission-preparation task.
