# Inventory for the estimated URL-case completion percentage

Inventory v1, October 5, 2026: **15 of 77 known cases complete — 19.5%.** See [progress.md](progress.md) for the current snapshot and six-hour update procedure. This inventory counts named URL cases with their required behavior; it is a provisional estimate, not a count of every distinct HTTP URL string or a percentage of engineering time.

The initial denominator combines 62 case specifications in the private discovery manifest, plus 20 later case names in private batch lists and the completed checklist, minus five aliases. The net additions are eight publication-profile cases and seven information pages. No private URL, record identifier or source response is copied here. The existing evidence in [checklist_completed.md](checklist_completed.md) supplies the completed states. Other rows remain pending even when partial or local evidence exists.

## Known aliases

| Discovery ID | Current canonical case |
| --- | --- |
| S01 | SEARCH01 |
| S08 | EMPTY01 |
| S09 | BROWSE01 |
| S10 | ADVANCED01 |
| I01 | HELP01 |

These names refer to the same already tracked cases; count each once. Scope-row IDs are a different field and must not be merged merely because their spelling matches a case ID.

## Cases

| Canonical case | Whole-case state |
| --- | --- |
| ABOUT01 | Complete |
| ADVANCED01 | Complete |
| BROWSE01 | Pending |
| C01 | Pending |
| D01 | Pending |
| D02 | Pending |
| D03 | Pending |
| D04 | Pending |
| E01 | Pending |
| EMPTY01 | Complete |
| FAQ01 | Complete |
| H01 | Pending |
| H02 | Pending |
| H03 | Pending |
| HELP01 | Complete |
| HELP_VIZ01 | Complete |
| HISTORY01 | Complete |
| I02 | Pending |
| I03 | Pending |
| I04 | Pending |
| L01 | Pending |
| L02 | Pending |
| L03 | Pending |
| L04 | Pending |
| L05 | Pending |
| L06 | Pending |
| L07 | Pending |
| O01 | Pending |
| O02 | Pending |
| O03 | Pending |
| O04 | Complete |
| O05 | Pending |
| O06 | Pending |
| P01 | Complete |
| P02 | Pending |
| P03 | Complete |
| P04 | Complete |
| P05 | Pending |
| P06 | Pending |
| P07 | Complete |
| P08 | Pending |
| P09 | Pending |
| P10 | Pending |
| P11 | Pending |
| P12 | Pending |
| P13 | Pending |
| P14 | Pending |
| P15 | Pending |
| PUBLICATIONS01 | Complete |
| R01 | Pending |
| R02 | Pending |
| R03 | Pending |
| ROADMAP01 | Complete |
| S02 | Pending |
| S03 | Pending |
| S04 | Pending |
| S05 | Pending |
| S06 | Pending |
| S07 | Pending |
| S11 | Pending |
| S12 | Pending |
| S13 | Pending |
| S14 | Pending |
| S15 | Pending |
| SEARCH01 | Pending |
| TERMS01 | Complete |
| V01 | Pending |
| V02 | Pending |
| V03 | Pending |
| V04 | Pending |
| V05 | Pending |
| V06 | Pending |
| V07 | Pending |
| V08 | Pending |
| V09 | Pending |
| V10 | Pending |
| V11 | Pending |

## Maintaining the estimate

Before changing a state to Complete, retain all required deployed functional and visual evidence, or the owner's explicit acceptance of a documented difference. Reopen regressions. Individual improvements, screenshots, viewport sizes, fragments and repeated deployments do not create completed cases.

Some original discovery entries describe overlapping journeys, interactions or supporting formats; reconcile them with the approved endpoint scope before treating this as a final inventory of unique URLs. Preserve required behavior when merging entries, and add newly established required URLs explicitly. Do not infer that a supporting case passes solely because its referring profile passes. Record every denominator change and its reason in the progress snapshot; keep unreconciled and blocked cases pending rather than remove them to improve the percentage.

Source references from the outer workspace are `public_site_review/planning/public_cases.json`, `url_batch_*/urls.json`, and the repository's completed checklist. Keep exact bindings and detailed evidence outside Git. New workspaces can use this safe list while recovering the separate private inputs. Complete integration, endpoint-family coverage and owner acceptance remain separate requirements.
