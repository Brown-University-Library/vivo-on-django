# Code retained for owner review

The owner asked to remove conversion-only code while protecting working behavior. The conversion review is complete. These items concern future cleanup, not unfinished conversion work.

The owner also requested removal of prepared/replay code. I retained it under the instruction to keep code when removal might affect working behavior: live imports and the test baseline still depend on these modules. A focused follow-up can separate shared helpers and test the affected behavior before removing the modes.

## Retained items

| Item | Why it remains | What later removal needs |
| --- | --- | --- |
| `prepared_data.py` and prepared mode | Live code imports PageDataError and MissingRecordError. Views, middleware, checks, and readers also use its classes. | Separate shared live errors/helpers, then retire prepared branches with tests for rendering, failures, and startup. |
| `recorded_responses.py` and replay mode | Live requests/parsers use RequestKey, RecordedResponse, and parsing. The retained comparison tool imports helpers here. | Preserve shared request/response types and HTTP bytes/status/headers; keep useful made-up-response tests. |
| `validate_prepared_data.py`, offline settings/guides | Existing modes still read their external files. Removing isolated commands/comments would leave them partly maintained. | Retire them with the mode after deciding which developer workflows need saved inputs. |
| Prototype mode, `display.py`, `home.py` | Views import these helpers. Home rendering uses BookCover; the test runner selects prototype mode before configuration loads. | Preserve shared values and choose a replacement test baseline before deleting sample branches. |
| Older/prepared-named templates and assets | Shared rendering uses them across modes. A filename does not establish that a file is unused. | Trace views and inheritance and check affected pages before deletion. |
| `trio` | No direct app import was found, but HTTP packages support asynchronous backends. Dependencies are unchanged in this cleanup. | Check backend use and package requirements separately; test source/challenge behavior before changing the lockfile. |
| Package version `0.0.0` | Release tag v1.0 is separate from package metadata. | Decide whether package versions should follow release tags. |
| Inherited ignore patterns | They may protect local files even when tracked code does not use them. | Confirm local uses before removing exclusions. |

Authentication/editing code and `config/tmp/restart.txt` remain as requested. This cleanup changed no routes, settings defaults, views, templates, static files, middleware, models, or migrations.

## Removed material

The five capture management commands, source-capture helpers, and validator script created or checked conversion inputs. Active application modules did not import them. Their seven capture/validator tests were retired; runtime parsing, rendering, failures, and reader tests remain.

`vivo_app/lib/visualization.py` supplied standalone sample classes imported only by `test_visualization.py`. Both were retired with three sample tests. Current graphs use retained source_graph/source_org_charts modules, views, templates, and scripts.

[Historical code](../historical_conversion_info/code/README.md) preserves reference copies as text files so imports and discovery cannot execute them. A verified copy of all pre-cleanup tracked files is also outside Git.

## Later decisions

Identify callers and protected behavior before further removal. Write a focused test before changing uncertain behavior, or retain the code and explain the concern here. Retired batch checklists do not become new tasks.
