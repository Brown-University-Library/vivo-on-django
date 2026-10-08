# Readable inventory of URL cases

Updated October 7, 2026. This is the active list of cases used for the completion estimate. Read each case's description and URL/request pattern beside its current whole-case state. See [progress.md](progress.md) for the single current global fraction and percentage, and [public_endpoint_scope.md](public_endpoint_scope.md#required-endpoints-and-data-sources) for required endpoint families and their case assignments.

Contents: [Known aliases](#known-aliases) · [Cases](#cases) · [Maintaining the inventory](#maintaining-the-inventory)

Paths are relative to the configured site; GET is assumed unless another method is stated. Placeholders stand for private bindings: person, organization, team, missing-record and other record IDs; file IDs, buckets, filenames and paths; query/filter values and page numbers. Repeated `{record_id}` means the same record in both positions. Query values require normal URL encoding. Follow actually offered links and recorded variations rather than inventing a URL by substituting arbitrary values.

Several cases share a pattern: they check different selected records, content variations, controls or entry/return journeys. A case may also include a document or supporting data request. The descriptions summarize its existing checks; they do not replace the passing conditions or permit completion based only on the listed visible page. Whole-case state means all required deployed functional and visual evidence passes, or the owner has explicitly accepted documented differences. Individual fixes and passing entry links do not complete their destination graph or format case.

The provisional denominator comes from 62 original discovery specifications plus 20 later case names minus five aliases. The net additions are eight publication-profile cases and seven information pages. This does not establish an exhaustive count of distinct URLs, complete endpoint-family coverage, integration success or final owner acceptance. Scope rows and case IDs are different fields even when their spelling matches.

The owner's October 6 exclusion of sixteen commented local account/editing routes removes no canonical case: none was in this inventory. Keep all current rows and states. Do not add these routes as pending cases or count their exclusion as completion. See [the exact excluded patterns](public_endpoint_scope.md#preserved-links-and-excluded-behavior).

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

| Canonical case | Human-readable check | URL pattern and required request variation | Whole-case state |
| --- | --- | --- | --- |
| ABOUT01 | About page, navigation and illustrations | `/about` | Complete |
| ADVANCED01 | Advanced search: name-only and combined name/title, then return | `/search/advanced`; submit `search=true`, `name_t={query}`, optionally `title_t={query}` → `/search?q={query}` | Complete |
| BROWSE01 | Browse without a term, including an empty search submission | `/search` and `/search?q=` | Pending |
| C01 | Direct browser-challenge page | GET `/challenge`; runtime POST and enforcement checks remain separate scope requirements | Pending |
| D01 | Linked CV document, delivery and viewer return | Follow `/display/{person_id}` → `/docs/{bucket}/{filename}.pdf` with observed query parameters → return to profile | Complete |
| D02 | Profile JSON, nested values and flags | `/display/{person_id}.json` | Pending |
| D03 | Organization publication download, complete TSV and headers | `/display/{organization_id}/publications.tsv` | Pending |
| D04 | Representative portrait, default portrait and homepage book-cover delivery | Actual linked `/profile-images/{path}`, `/book_cover/{path}` or `/assets/{path}`, inspected with the consuming profile or `/` | Complete |
| E01 | Missing record, not-found response and recovery | `/display/{missing_record_id}` → home/search recovery; other missing-page variations remain scope checks | Complete |
| EMPTY01 | No-result search, message and recovery controls | `/search?q={query}` with a privately recorded no-result query | Complete |
| FAQ01 | FAQ page and every offered anchor | `/faq` and observed section fragments | Complete |
| H01 | Homepage search, carousel, author links and navigation | `/` → `/search?q={query}` or linked `/display/{person_id}` → return | Pending |
| H02 | Homepage carousel boundaries, wrap, final short group and keyboard use | `/`; Previous/Next, settled groups and linked images | Pending |
| H03 | Homepage background selection and reload behavior | `/`; normal reloads and the actually selected background asset | Complete |
| HELP01 | Help page, navigation and illustrations | `/help` | Complete |
| HELP_VIZ01 | Visualization help page and links | `/help/viz` | Complete |
| HISTORY01 | History information page and links | `/history` | Complete |
| I02 | Institution information page, illustration and internal links | `/brown` and observed slash entry | Pending |
| I03 | Normal status JSON and required response checks | `/status`; controlled failures and routing ownership remain separate scope checks | Pending |
| I04 | Public faculty-service trailing-slash redirect | `/services/data/v1/faculty/{person_id}` → same path with trailing slash; service internals are excluded | Pending |
| L01 | Legacy individual and people/organization entries with rendered destinations | GET `/individual/{record_id}`, Accept `text/html` → `/display/{record_id}`; `/people` and `/ous` → `/search?fq={filter}` | Pending |
| L02 | Bare display entry redirects to browse search | `/display/` → `/search`; confirm handling of incoming parameters | Pending |
| L03 | Old search query parameter redirects to the current query | `/search?querytext={query}` → `/search?q={query}` | Pending |
| L04 | Public report entry redirects to home | `/reports/subject-lib` → `/`; retain recorded entry-state and slash/query checks; authenticated reports are excluded | Pending |
| L05 | Exact JSON Accept header selects the JSON-LD redirect | GET `/individual/{record_id}`, Accept `application/json` → `/individual/{record_id}/{record_id}.jsonld` | Pending |
| L06 | Exact Turtle Accept header selects the Turtle redirect | GET `/individual/{record_id}`, Accept `text/turtle` → `/individual/{record_id}/{record_id}.ttl` | Pending |
| L07 | Old image link redirects to the working portrait | `/file/{file_id}/{filename}` → `/profile-images/{path}` | Complete |
| O01 | Organization with administrative/faculty role groups and member return | `/display/{organization_id}` → linked `/display/{person_id}` → browser Back | Pending |
| O02 | Organization entered from filtered search, prose and external links | `/search?fq={filter}` → `/display/{organization_id}` | Complete |
| O03 | Additional organization overview and role-group variation | `/display/{organization_id}` | Complete |
| O04 | Organization without member rows or a visualization entry | `/display/{organization_id}` with no member groups or graph control | Complete |
| O05 | Organization with custom membership | `/display/{organization_id}`; configured membership, member links and offered graph entry | Complete |
| O06 | Approved active-team member list and default image | `/display/{team_id}`; observed member links and offered graph entry | Complete |
| P01 | Primary profile: sections, View All, search return and linked CV | `/display/{person_id}` and section fragments, including `#All`; linked CV and referring search | Complete |
| P02 | Profile entered from an organization, sections and return journey | `/display/{organization_id}` → `/display/{person_id}` and `#All` → return to organization | Complete |
| P03 | Profile entered from search, publication filters and search return | `/search?q={query}` → `/display/{person_id}` and section fragments → referring search | Complete |
| P04 | Profile with Teaching, View All and an education-institution link | `/display/{person_id}` and `#All` → institution's fielded `/search?q={query}` → browser Back | Complete |
| P05 | Profile entered from search, scholarly work and View All | `/search?q={query}` → `/display/{person_id}` and `#All` → referring search | Complete |
| P06 | Profile with Book filtering, View All and linked CV | `/display/{person_id}` and `#All`; offered publication filters and linked `/docs/{bucket}/{filename}.pdf` | Complete |
| P07 | Sparse profile, portrait and available controls | `/display/{person_id}` and only offered sections | Complete |
| P08 | Additional full profile, publication filters, graph entries and CV | `/display/{person_id}` and offered section fragments, links and linked CV | Complete |
| P09 | Additional profile with a CV and its available sections | `/display/{person_id}` and offered section fragments, links and linked CV | Complete |
| P10 | Additional profile, undated credentials and publication filters | `/display/{person_id}` and offered section fragments and links | Complete |
| P11 | Additional profile, open appointments, CV and department destinations | `/display/{person_id}` and offered sections → linked `/display/{organization_id}` and CV | Complete |
| P12 | Additional profile, publication filters and graph-entry controls | `/display/{person_id}` and offered section fragments and links | Complete |
| P13 | Additional profile, book-citation formatting, CV and department destination | `/display/{person_id}` and offered sections → linked `/display/{organization_id}` and CV | Complete |
| P14 | Additional profile, quoted citations, CV and department destination | `/display/{person_id}` and offered sections → linked `/display/{organization_id}` and CV | Complete |
| P15 | Additional profile with publication filters and no CV control | `/display/{person_id}` and offered section fragments, links and graph entries | Complete |
| PUBLICATIONS01 | Publication help page and links | `/publications`; this is an information page | Complete |
| R01 | Original VIVO JSON-LD representation | `/individual/{record_id}/{record_id}.jsonld` | Pending |
| R02 | Original VIVO Turtle representation | `/individual/{record_id}/{record_id}.ttl` | Pending |
| R03 | Original VIVO RDF/XML representation | `/individual/{record_id}/{record_id}.rdf` | Pending |
| ROADMAP01 | Roadmap information page and links | `/roadmap` | Complete |
| S02 | Applying/removing a filter resets the result page | `/search?q={query}&page={page}`; apply/remove the recorded filter | Pending |
| S03 | Affiliation More dialog: groups, sorting, narrowing and selection | `/search?q={query}`; affiliation dialog and `/search_facets` requests with search inputs and `f_name={filter}` | Pending |
| S04 | Research/publication More dialogs and filtered no-result search | `/search?q={query}`; research/publication dialogs and `/search_facets` requests with search inputs and `f_name={filter}` | Pending |
| S05 | Combined filters and removing one while retaining another | `/search?q={query}&fq={filter}&fq={filter}`; repeated `fq` values and recorded selection/removal journey | Pending |
| S06 | Pagination, last/previous page and browser Back/Forward | `/search?q={query}&page={page}` | Pending |
| S07 | Later-page search result, profile entry and Back to search | `/search?q={query}&page={page}` → `/display/{person_id}` → original search | Pending |
| S11 | Search JSON array, record order and response metadata | `/search?q={query}&format=json` | Pending |
| S12 | Supported Advanced department parameter | `/search/advanced?search=true&department_t={query}` → `/search?q={query}`; no new visible field | Pending |
| S13 | Title-only Advanced submission and retained form values | `/search/advanced?search=true&name_t=&title_t={query}` → `/search?q={query}` → browser Back | Pending |
| S14 | Empty Advanced submission stays on the form | `/search/advanced?search=true&name_t=&title_t=`; no redirect to browse results | Complete |
| S15 | Affiliation More dialog keyboard opening, Escape and focus return | `/search?q={query}`; affiliation dialog keyboard journey | Complete |
| SEARCH01 | Keyword results, count/order, facets and search-match controls | `/search?q={query}`; recorded filters and page variations use repeated `fq`, `fq_0` and `page` | Pending |
| TERMS01 | Terms information page and links | `/termsOfUse` | Complete |
| V01 | Organization collaboration graph, scope/labels and linked JSON | `/display/{organization_id}/viz/collab` and `.json` → organization return | Pending |
| V02 | Empty person collaboration graph and recovery controls | `/display/{person_id}/viz/collab`, `.json`, `.csv`; empty-data variation, supporting formats and image controls | Pending |
| V03 | Empty person coauthor graph reached from collaboration | `/display/{person_id}/viz/collab` → `/display/{person_id}/viz/coauthor` and `.json`; empty-data variation | Pending |
| V04 | Populated person collaboration entry, expansion, labels and fit | `/display/{person_id}` → `/display/{person_id}/viz/collab`, `?fit=1`, `.json`, `.csv` | Pending |
| V05 | Populated person coauthor graph, expansion and generated SVG | `/display/{person_id}/viz/collab?fit=1` → `/display/{person_id}/viz/coauthor`, `.json`, `.csv` | Pending |
| V06 | Person coauthor keyboard controls, PNG/SVG and fit reset | `/display/{person_id}/viz/coauthor` and `?fit=1`; browser-generated PNG/SVG, not separate server endpoints | Pending |
| V07 | Person graph pointer/details, drag, neighbor navigation and exports | `/display/{person_id}/viz/collab` and `/display/{person_id}/viz/coauthor`; neighbor person IDs and browser Back | Pending |
| V08 | Organization graph keyboard scope controls and SVG/PNG exports | `/display/{organization_id}/viz/collab`; browser-generated SVG/PNG | Pending |
| V09 | Person coauthor treemap and ordinary coauthor data links | `/display/{person_id}/viz/coauthor_treemap`; `/display/{person_id}/viz/coauthor.json` and `.csv` | Pending |
| V10 | Organization publication-history chart, ranges and formats | `/display/{organization_id}/viz/publications`, `.json`, `.csv` | Pending |
| V11 | Organization research-area chart, SVG and supporting JSON | `/display/{organization_id}/viz/research` and `.json`; visible download remains `/display/{organization_id}/viz/collab.json` under the deferred issue | Pending |

## Maintaining the inventory

When a case state, route/request variation or description changes, update that same row. When an approved case is added or an alias is reconciled, preserve required behavior and record the reason in [progress.md](progress.md#update-rules). Keep blocked, partial and unverified cases pending; do not remove them to improve the percentage. Count by column headers rather than a fixed column position.

Retain passing conditions and detailed evidence in the case records, completed checklist and private workspace. Reopen regressions; preserve applicable evidence for unaffected checks with its revision and reason. Put shared-difference investigations in [current_batch.md](current_batch.md#shared-differences), not appended global snapshots here. Historical state transitions are retained in the checklists, batch records and [pre-cleanup inventory](previous_workplan_artificts/inventory_before_readable_patterns_2026_10_06.md).

Update the scope document when required behavior changes or case assignments are reconciled. Its assignment column does not duplicate case status: current state remains in this table. Supporting formats, runtime challenge/failure behavior, source/asset integration and owner acceptance still need their own evidence. Unassigned variations stay explicitly pending in scope and checklist records; do not infer coverage solely from a complete referring page.

Private sources are `public_site_review/planning/public_cases.json`, its evidence bindings and `url_batch_*/urls.json` in the outer workspace. Recover exact bindings privately in a new workspace. Keep names, actual record IDs, query/filter values, hosts, raw responses and visual artifacts out of tracked files. Maintain safe descriptions and patterns here so people can understand the measure without those inputs.
