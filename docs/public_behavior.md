# Public application behavior

The owner completed the conversion review in October 2026. Preserve the reviewed application's URLs, query meaning, visible content, navigation, and response formats. `config/urls.py` defines registered routes; `vivo_app/views.py` coordinates responses.

## Pages and responses

Paths below are relative to the application's configured browser prefix. IDs, query values, and filenames are placeholders.

| Endpoint family | Behavior to preserve | Live source |
| --- | --- | --- |
| `/` | Search entry, navigation, changing background, book carousel, and author links. | Separate book database and cover images; local backgrounds. |
| `/search`, `/search/advanced`, `/search_facets` | Search text, repeated filters, result order, pagination, highlighting, More dialogs, advanced redirects, and browser history. Preserve older querytext redirects. | Solr. |
| `/search?…&format=json` | Existing JSON values, types, order, and encoding. | Solr. |
| `/display/{id}` | Person sections, publication filters, organization groups, member links, teams, portraits, graph and document links. | Solr, images, graph availability, and membership definitions. |
| `/display/{person_id}.json` | Profile JSON handled by the display view, distinct from VIVO JSON-LD. | Solr and graph availability. |
| `/display/{organization_id}/publications.tsv` | Publication rows, columns, bytes, and download metadata. | Solr membership and faculty data. |
| `/display/{id}/viz/…` | Graphs, treemaps, publication/research charts, controls, exports, and empty states. | Visualization service or calculations from Solr. |
| `/individual/{id}/{id}.{format}` and registered legacy forms | JSON-LD, Turtle, RDF/XML, applicable redirects, Accept handling, and original bytes. | VIVO/Vitro. |
| `/source-images/…`, `/source-documents/…`, `/docs/…`, `/file/…` | Images, documents, PDFs, supported redirects, and legacy links. | Configured sources or saved inputs. |
| `/display/`, `/people`, `/ous`, `/individual/{id}` | Existing redirects and their reviewed destinations. | Redirects and destination data. |
| Informational pages | About, Help, FAQ, terms, history, roadmap, publications, visualization help, institution pages, aliases, and anchors. | Templates and assets. |
| `/reports/subject-lib` | In source modes, redirect home rather than render the separate report workflow. | No report source read for this entry. |
| `/challenge` | Configured Turnstile flow, disabled behavior, and sessions. | Turnstile for a configured challenge. |
| `/status`, `/version/` | Status/error behavior and distinction between checkout and loaded revisions. | Solr for status; local revision data for version. |
| `/services/data/v1/faculty/{id}` | Registered handoff to the separate data service. | Existing service outside this webapp. |

Use exact registered routes for suffixes and slash aliases. Keep export routes before the generic individual redirect. An HTTP 200 alone does not establish correct content or download metadata.

## Supporting services and boundaries

The webapp reads existing services. It does not rebuild Manager, provision Solr, or implement VIVO. External destinations remain separate workflows.

Account/editing routes commented out in `config/urls.py` remain disabled. Their code, templates, models, and migrations are retained at the owner's request. The installation's Shibboleth restriction is managed separately; future browser checks use the access already arranged.

## Data modes and maintenance

Live mode reads configured services. Prepared, replay, and prototype modes remain because of shared helpers and test setup; [the review note](code_retirement_review.md) explains why. Source failures and missing saved inputs must retain their existing error behavior.

Use [development checks](development_checks.md) for changes and [source configuration](source_journey.md) for settings. [Historical scope](../historical_conversion_info/original_scope/public_endpoint_scope.md) explains selection of the conversion endpoints; old case statuses are not a current backlog.
