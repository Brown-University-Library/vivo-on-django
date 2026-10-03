# Current batch and URLs being evaluated

Follow [workplan.md](workplan.md). Keep this file current so the next conversation can resume without reconstructing the batch. Archive a dated safe copy in [previous_workplan_artificts/](previous_workplan_artificts/) after evaluation, then start the next batch here. Preserve detailed evidence and exact URL bindings privately.

Contents:

- [Batch status](#batch-status)
- [Current URL cases](#current-url-cases)
- [Changes in this batch](#changes-in-this-batch)
- [Handoff and evaluation](#handoff-and-evaluation)

## Batch status

- Batch ID: not selected.
- State: not evaluated; workplan setup only.
- Started / last updated: October 3, 2026.
- Goal: finish one selected URL's required behavior and appearance, where possible.
- Branch / starting revision: not recorded; fill before implementation.
- Planned change count: 0 of a maximum of 30.
- Completed local changes: 0.
- Commits / pushed revision: none for this setup.
- Push result / date: not pushed.
- Owner deployment confirmation / date: pending for a future batch.
- Loaded deployed revision / check date: not checked.
- Next responsible person and action: Codex reconciles existing evidence, checks for outstanding deployment/evaluation, and selects the first URL.

## Current URL cases

No URLs are selected for evaluation yet. Add one row for every selected case before making its changes. Bind the case to exact Rails and Django URLs in `../../current_urls.local.md`, in the outer/stuff directory outside the project repository. Include supporting URLs and required variations; record fragments, parameters, methods, and headers privately where they identify a record.

| Pending ID / case ID | Safe URL pattern and variation | Expected Rails behavior | Required post-deployment comparison | Result / evidence label / next action |
| --- | --- | --- | --- | --- |

## Changes in this batch

Add at most thirty rows. Count a specific fix or outcome as one change even when it affects several files. Record which current URL cases it addresses; do not count tests or tracking-file updates as separate fixes merely to reach thirty.

| Change ID | Case IDs | Observed difference and intended result | Local check and result | Commit | Deployed check and result | Remaining difference / next action |
| --- | --- | --- | --- | --- | --- | --- |

## Handoff and evaluation

1. Before pushing, review the exact diff for sensitive information and run the checks required by `../AGENTS.md`. Record their commands and safe result summaries here; detailed logs stay private. Commit related files using that file's message guidance, then push the batch under the owner's implementation-batch authorization.
2. Record commit IDs and the push result. Tell the owner the batch is pushed and ready for the owner to run the deploy script. If the push fails, retain the current URLs and record what remains to be pushed.
3. Wait for the owner's deployment confirmation. Record it, verify the loaded revision, and evaluate every current case and changed behavior against Rails. An unavailable page or untested interaction remains blocked or needing review.
4. Move verified cases to `checklist_completed.md`. Update `checklist_todos.md` with every remaining difference, blocked check, or unfinished variation. Record relevant checks of previously completed URLs when shared code changed.
5. Report per-URL and per-change outcomes. Archive this batch's safe record, preserve private exact bindings, and use the remaining differences to select the next batch. Prefer finishing the same URL before extending a feature across other URLs.

Local checks: not run for a future implementation batch.

Related completed URLs requiring regression checks: select when changes are known.

Evaluation summary and next-batch candidates: pending.
