# Rails-to-Django conversion summary

## Progression

1. **Start with a prototype.** Early plans proposed mapping every Rails route. Shared layout, information pages, and sample records made local rendering and tests possible.
2. **Choose the public behavior to preserve.** The owner-approved September 26 scope focused on functionality actually used by the public frontend. Manager workflows and the VIVO backend remained separate services.
3. **Develop pages with prepared inputs.** Saved page fields and assets allowed offline layout and interaction work. A bundle's coverage was explicit; missing requests did not become sample pages.
4. **Replay original source responses.** Request keys, headers, unchanged bytes, and checksums let the same parsing and page-building code run with saved responses or live services.
5. **Connect live sources.** Solr supplied searches, profiles, and memberships; separate sources supplied images, documents, graph data, VIVO formats, and homepage books. Custom graph/chart processing remained application code.
6. **Compare behavior and appearance.** Browser checks covered navigation, controls, download responses, complete views, and resources. Font work illustrated why matching text or file hashes alone does not establish identical rendering.
7. **Finish with owner review.** After v1.0, the owner manually reviewed many URL comparisons and made code changes. On October 9 the owner said no unfinished conversion work remained. Old batch percentages were not recalculated and do not describe that final review.

## Useful lessons

Keep runtime processing separate from tools that gather comparison inputs. Use made-up data in repository tests and keep real records outside Git. Record exactly what a saved input covers; missing states should fail visibly.

Compare source data separately from rendering. Preserve required formats, redirect behavior, repeated query values, ordering, and literal destinations. Keep ordinary full views beside focused screenshots used to isolate a layout cause.

Narrow owner choices should remain narrow. A historical comparison finding is not permission to redesign unrelated behavior.

## Repository transition

Detailed work logs moved outside Git. Current guides describe application operation and future changes. Source-capture commands/helpers, their seven tool tests, and the standalone sample visualization module/tests were retired. Reference source remains here as text.

Shared prepared/replay/prototype code was retained because live imports and test setup still depend on it. [The review note](../docs/code_retirement_review.md) records those dependencies without reopening conversion work.
