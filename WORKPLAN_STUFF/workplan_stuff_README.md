# Guide to WORKPLAN_STUFF

## Brief overview

These files define the approved scope, guide improvements and record completion evidence. Start with [progress.md](progress.md) for the current percentage, then [url_completion_inventory.md](url_completion_inventory.md) for readable URL patterns and case status. Read [public_endpoint_scope.md](public_endpoint_scope.md) for broader requirements and [workplan.md](workplan.md) for the working procedure.

Contents: [Brief overview](#brief-overview) · [Active files](#active-files) · [Historical files](#historical-files)

## Active files

| File | Purpose | Update when |
| --- | --- | --- |
| [GOAL.md](GOAL.md) | Defines the intended outcome, exclusions and final acceptance requirements. | The owner changes the goal or accepts a scope decision. |
| [workplan.md](workplan.md) | Explains who performs each step, where results belong, and how work continues and stops. | The workflow changes. |
| [accepted_differences.md](accepted_differences.md) | Records explicit owner choices about reference problems and precisely scoped visual differences, separately from implementation and verification. | The owner decides an individual case, approves an affected check definition or its implementation/verification state changes. |
| [public_endpoint_scope.md](public_endpoint_scope.md) | Lists approved endpoint patterns, required behavior, sources, case assignments and exclusions. | A requirement, known dependency or case assignment changes. |
| [url_completion_inventory.md](url_completion_inventory.md) | Lists each counted case, readable URL/request pattern, required variation, current state and aliases. | A case's state, description, pattern, variation or alias changes. |
| [progress.md](progress.md) | Shows the single current global completion percentage and concise snapshot history. | Case totals change or a scheduled/start/resumption/handoff snapshot is due. |
| [completion_checks.md](completion_checks.md) | Explains the measures, records the approved RC01 procedure for repeated checks and preserves original definitions, including P01. | A demonstrated requirement or agreed check definition changes. |
| [current_batch.md](current_batch.md) | Records the current pass's changes, shared differences, releases and verification results. | A change is recorded, released, verified or blocked by a new finding. |
| [next_batch.md](next_batch.md) | Lists up to twenty active cases and their concrete actions; keeps a separate parked list with blockers, recovery conditions and evidence pointers. | Active membership changes, a case is parked or can resume, or remaining actions change. |
| [checklist_todos.md](checklist_todos.md) | Tracks pending scope comparisons, integration checks and final acceptance tasks. | Work is added, completed, reopened or gains a different next action. |
| [checklist_completed.md](checklist_completed.md) | Records completed work and evidence; identifies reopened cases. | Whole cases or other tracked milestones complete or reopen. |
| [workplan_stuff_README.md](workplan_stuff_README.md) | Explains every top-level file's job and distinguishes active records from history. | A file is added, retired, moved or changes purpose. |

Keep the live global fraction/percentage only in progress.md. The inventory holds case state and readable patterns together; other files hold evidence or next actions and link to the dashboard. Dated historical results and case-specific check counts may remain in their records. Different cases can use the same pattern; completing one example does not complete its endpoint family. Exact bindings and detailed private evidence stay outside Git.

The outer workspace also keeps `../../post_exact_behavior_review.local.md`. It holds pending reference-problem observations and detailed private evidence for the owner's choice between reproducing Rails and implementing a specific expected outcome. Earlier deferral wording is historical unless it records an explicit owner decision that still applies. The file remains outside Git; accepted choices receive safe summaries in [accepted_differences.md](accepted_differences.md). Pending observations alone authorize no implementation or acceptance.

The private [../../owner_review_queue.local.md](../../owner_review_queue.local.md) stores prepared comparisons, stable review IDs, pending decisions and the last unsolicited notice timestamp and announced items. Follow [optional owner comparison reviews](workplan.md#optional-owner-comparison-reviews) for the rolling hourly limit and owner-led review. Saved evidence and exact URLs stay outside Git; precisely scoped accepted choices belong in accepted_differences.md. Available reviews do not pause independent work or complete a case.

Follow [repeated data and controls](workplan.md#check-repeated-data-and-controls-efficiently) before another exhaustive audit of equivalent items. Complete data comparisons stay required. Codex records affected check revisions, selects normal and edge examples at both widths, preserves valid evidence and finishes remaining distinct-state checks. This procedure accepts no difference or whole case by itself.

## Historical files

[previous_workplan_artificts/](previous_workplan_artificts/) preserves earlier plans, batch records and evaluation reports. Its spelling follows the original setup. These files explain past decisions and results; do not update them as current instructions or current totals.

| File group | What it preserves |
| --- | --- |
| `PLAN__workplan.md`, `PLAN__workplan_v2.md` | Earlier workflow versions. |
| `batch_*_current_batch.md`, `batch_*_evaluation.md` | Earlier work counted by individual improvements. |
| `url_batch_*_current_batch.md`, `url_batch_*_next_batch.md`, `url_batch_*_evaluation.md` | Earlier URL-based selections, changes and review outcomes. |
| `url_batch_*_final_current_batch_*.md`, `url_batch_*_final_next_batch_*.md` | Final pass accounting and unfinished selections preserved when a new dated run begins. |
| `progress_before_simplification_*.md` | Detailed history and measurements from the original progress page. |
| `inventory_before_readable_patterns_*.md` | The original case states, aliases and historical shared-check updates before adding readable patterns. |

Keep dated results in these records. Use the active inventory and progress page for current case status and totals.
