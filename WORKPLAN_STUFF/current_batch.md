# Current batch and URLs being evaluated

Follow [workplan.md](workplan.md). Exact URLs remain in `../../current_urls.local.md`, outside Git. Private evidence label: `batch-002-profile-checks`. The [first-batch record](previous_workplan_artificts/batch_001_current_batch.md) and [deployed evaluation](previous_workplan_artificts/batch_001_evaluation.md) preserve the previous results.

Contents:

- [Batch status](#batch-status)
- [Current URL cases](#current-url-cases)
- [Changes and required deployed checks](#changes-and-required-deployed-checks)
- [Local validation](#local-validation)
- [Handoff](#handoff)

## Batch status

- Batch ID: batch-002; updated October 3, 2026.
- State: ready for deployment after Codex confirms the push; implementation and local checks complete.
- Branch / starting revision: `main` / `e0cec5a`.
- Changes: 3 focused outcomes, addressing demonstrated differences under S07.
- Application commit: `75269fc` (`Preserves empty profile sections and citation spacing`).
- Owner deployment confirmation: pending.
- Deployed results for this batch: pending; local checks do not certify deployed behavior.

The primary profile remains the preferred case to finish. Its remaining browser checks encountered an expired sign-in, a stalled native-control call, and then an extension interface blocking automation after the owner signed in again. These are review dependencies, not new application differences. Preserve its twenty checks in [progress.md](progress.md); no matched visual checks were completed during this implementation pass. Proceed with the already demonstrated sparse-profile and citation differences while that browser dependency is unresolved.

## Current URL cases

| Case | Scope and safe route | Purpose |
| --- | --- | --- |
| P01 | S07 `/display/{person_id}` | Primary profile; recheck content, controls, keyboard use, supporting links, and all defined desktop/narrow views. |
| P04, P07 | S07 `/display/{person_id}` | Empty panels in View All, fresh bookmarks, conditional buttons, and desktop/narrow appearance. |
| P10 | S07 `/display/{person_id}` | Five demonstrated chapter-collection spacing differences. |
| P08, P09, P11, P12 | S07 `/display/{person_id}` | Publication text, inline formatting, links, and filter regression comparisons. |

## Changes and required deployed checks

| Change | Result implemented | Local evidence | Required deployed confirmation |
| --- | --- | --- | --- |
| batch-002-01 | Preserve source spacing inside italic chapter collection titles; keep whitespace-only titles absent and preserve safe inline formatting. | Citation regression cases pass. All 278 selected saved citation texts match Rails; 3,808-citation differences decrease from 39 to 25, with no regressions. | Compare P10 rows 5, 18, 33, 44, and 55 and the same full 278-citation sample. Inspect Publications visually at desktop and narrow widths. |
| batch-002-02 | Keep empty Background, Affiliations, and Teaching panels in the proper order while their navigation buttons remain absent without content. | Sparse and populated model/template regressions pass; existing prepared profiles retain their section fallback. | Compare P04/P07 View All, headings, conditional buttons, and full relevant content at desktop and narrow widths. |
| batch-002-03 | Select an existing empty panel from its bookmark; support a fresh View All bookmark even without a View All button. | Thirteen JavaScript initial-state cases and return-to-Overview interactions pass, including absent buttons, populated panels, and unknown-section fallback. | Reload fresh P04 Affiliations and P07 Background/Affiliations/Teaching/All bookmarks. Compare visible panels and active buttons with Rails; then confirm ordinary controls and keyboard selection on P01. |

## Local validation

- Full Django suite: 267 tests pass, including two new regression methods and a sparse-profile integration assertion.
- Ruff lint and formatting: all three changed Python files pass.
- Pyright: all three changed Python files pass with zero errors or warnings, using the project interpreter and basic checking; Pylance is unavailable.
- JavaScript syntax check and thirteen section-state cases: pass. These execute the actual script against controlled page elements; they do not establish visual browser equivalence.
- Saved source comparisons: 278/278 selected citation texts match; broader 3,808-citation comparison has 25 remaining differences, down from 39, with fourteen newly matching and zero regressions. This compares current local output with saved reference data, not a fresh deployment.
- Tracked examples use made-up names and records; real data stays outside Git. Private evidence and the resume checkpoint are in the outer workspace.

## Handoff

1. Codex finishes local checks, reviews the outgoing changes, commits related application files together, then commits the safe workplan records and pushes both commits.
2. The owner deploys the latest pushed revision and reports completion.
3. Codex verifies the loaded revision, repeats the exact affected checks above, and resumes P01's fixed twenty-check list when browser automation is available. Preserve paired evidence under matching viewport and scroll conditions.
4. Codex updates [progress.md](progress.md) and the checklists with newly passing checks, resolved differences, regressions, and remaining limits. Every required URL-pattern endpoint must eventually receive visual confirmation against Rails. Whole URLs remain pending until their required checks pass or the owner explicitly accepts a documented difference.

Carry forward batch-001's fourteen absent source variations and its blocked before-script check. Do not seek the previously rejected page-source result through another browser or tool. They do not prevent implementing the independently demonstrated differences in this batch.
