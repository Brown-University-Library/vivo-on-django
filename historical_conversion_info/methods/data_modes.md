# From samples to live sources

The conversion used four modes with different purposes:

| Mode | What it supplied | What it could establish |
| --- | --- | --- |
| Prototype | Sample records and pages. | Local startup, templates, and focused made-up-data tests. |
| Prepared | Already-arranged page fields and saved assets. | Layout and interaction behavior for exact listed requests. |
| Replay | Original saved source response bytes matched to exact request keys. | Repeatable processing through the same readers/parsers used for live data. |
| Live | Requests to the configured services and homepage book database. | Current integration and output for the chosen sources. |

Prepared pages were not raw source responses. Replay preserved request meaning, repeated parameter order, status/headers, and checksums; it never silently contacted a live service for missing inputs. Capture helpers paced and limited requests and wrote their manifests after gathering required responses.

This separation made it possible to investigate layouts without repeatedly querying services and to distinguish source changes from rendering changes. Private real records and captures stayed outside Git.

The retired capture/validator source is in [the code archive](../code/README.md). The active application still shares errors, request/response classes, and test setup with these modes; current [retirement notes](../../docs/code_retirement_review.md) explain why their removal was deferred.
