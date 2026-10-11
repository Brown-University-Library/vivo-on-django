# Code retained for owner review

The application reads its configured sources through one request path. Shared page errors are in `vivo_app/lib/page_errors.py`; request/response values and external-input checks are in `vivo_app/lib/source_types.py`. The membership reader and browser comparison tool still use those checks. Tests provide made-up source responses to application processing and rendering.

The following items remain separate maintenance decisions. Do not remove them as part of unrelated cleanup.

| Item | Why it remains | What a later change needs |
| --- | --- | --- |
| `render_or_stub()` | Informational pages and error handlers use its JSON and template-failure behavior. | Check actual responses before changing this shared helper. |
| Unsupported public routes | Existing routes retain their unavailable responses. | An explicit behavior decision before implementing or retiring those URLs. |
| `trio` | HTTP packages support asynchronous backends; no direct application import was found. | Check backend use and package requirements before changing dependencies. |
| Package version `0.0.0` | Release tags are separate from package metadata. | Decide whether package versions should follow release tags. |
| Inherited ignore patterns | They may protect local files even when tracked code does not use them. | Confirm local uses before removing exclusions. |

Disabled account/editing routes and their supporting code, models, and migrations remain as requested. `config/tmp/restart.txt` remains unchanged. Accepted public behavior is documented in [behavior decisions](behavior_decisions.md).

Before further removal, identify callers and the behavior they protect. Run focused tests and the [required checks](development_checks.md); a successful status code alone does not establish correct content or appearance.
