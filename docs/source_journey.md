# Source-backed search, profile, organization, and team journeys

The live journey requests a Solr search, opens a person profile and an ordinary linked organization, and looks up member portraits in one additional Solr request. It also serves search JSON, organization publication TSV, full search facet values, organization publication and research charts, a status count, and a supported profile CV PDF. A selected active team uses member IDs kept in a separate file outside Git. Graph JSON routes use a separate visualization source when it is configured. VIVO JSON-LD, Turtle, and RDF exports use a separately configured backend. Replay reads exact saved responses and runs the same page-building code without a network connection. Prepared mode remains the choice for the homepage and broader saved coverage.

## Contents

- [Configure a local source](#configure-a-local-source)
- [Additional formats and team data](#additional-formats-and-team-data)
- [Capture and replay one journey](#capture-and-replay-one-journey)
- [Capture and replay visualization data](#capture-and-replay-visualization-data)
- [Compare the result](#compare-the-result)
- [Current limits](#current-limits)

## Configure a local source

Set `SOLR_URL` to a reachable Solr core or collection URL, including its final name. Set `IMAGES_URL` to the base address that serves profile images. Set `DOCUMENTS_URL` to the origin that serves profile CV PDFs if those links should pass through Django. For public-page visualization work, set `VIZ_SERVICE_URL` to the public production visualization root ending in `/data/viz`, not the staging service. Set `VIVO_BACKEND_URL` to the original VIVO/Vitro origin when export routes need live responses. Keep exact source addresses in the private environment file. The source values in `example.env` are blank deliberately. Check source access from each machine that runs Django; workstation access alone does not prove development-server access.

Use `PAGE_DATA_MODE=live` for live search, person profile, and ordinary organization requests. This mode reads the configured sources at request time. It does not require a prepared bundle. Django startup checks verify configuration without contacting the sources; a successful check alone does not establish connectivity. The supported HTML routes are `/search?q=...` and `/display/ID`; `/search_facets?f_name=FIELD&q=...` returns all values for one supported facet. Search accepts a page number and repeated `fq=FIELD|VALUE` filters for the four listed facets. An unsupported option returns 503 instead of sample content.

## Additional formats and team data

`/search?q=...&format=json` uses the same Solr request as HTML search. `/display/ORG_ID/publications.tsv` makes one additional bounded member-record request and returns the public column names and download headers. A saved public organization TSV and a local source-backed TSV had the same 1,355 data rows by content; their row order differed between capture dates. A second fixed-member organization export matched all 272 public rows by content, again with a different order. The public profile JSON shape requires Solr metadata and visualization-availability lists. `/display/PERSON_ID.json` now converts nested publications, appointments, credentials, training, and collaborators; a made-up local test covers those fields. Three varied nested profiles were compared with saved public JSON and Solr responses. One matched 33 of 35 top-level fields, including all publications, appointments, training, and collaborators in order; its web-link field and update timestamp differed. A second matched 29 of 35 fields after correcting equal-date credential order; all 97 publications present in both responses matched exactly, while the public response contained 14 more publications than Solr. An earlier comparison matched 28 of 35 fields; its older public capture has changed source values and its image URL differs from the local route. One earlier sparse profile matched 34 of 35 public fields; its source update date changed between captures.

An active team or fixed-member organization may use `TEAM_SOURCE_MANIFEST`, a JSON file outside Git that records names and member IDs defined in Rails. The file has this shape with made-up names and records in the example:

```json
{"teams": {"team-example": {"name": "Example Team", "member_ids": ["invented-a", "invented-b"]}}, "organizations": {"org-example": {"extra_member_ids": ["invented-b"]}}}
```

The selected team page requests those members in one Solr call and uses the organization layout. A local replay showed the same four member names and titles as the saved public page, though the order differed between capture dates. One fixed-member organization adds configured people to the members supplied by its Solr record; its 13 displayed members matched the saved public page. A configured ID absent from Solr is skipped, as in Rails. The dynamic research-area organization combines externally defined members with a bounded research-area Solr query; its 74 displayed names matched the saved public page. One title changed between captures. The full public team variation still needs visualization support. Keep the actual definition file outside Git.

`/display/ID/viz/collab.json` and `/display/ID/viz/coauthor.json` use `VIZ_SERVICE_URL` for ordinary live graph data. The corresponding HTML pages read a Solr record for the heading and render source nodes and links in an interactive SVG. The page has the public network-scope, labels, details, fit, embed, and PNG controls; the direct `.csv` paths write the public graph columns as plain text. Selected production person and organization CSV downloads matched Django's replayed output byte for byte after correcting line endings. Direct production checks now cover both availability lists, a populated person coauthor graph, an empty person collaborator response, and an ordinary organization graph. Five upstream responses were captured outside Git and replayed through the same request construction and parsing. The empty collaborator response remains an HTTP 200 `{}` with an empty CSV and a visible empty-state message on the page. Selected person and organization network pages were also compared in a desktop browser. Their headings, descriptions, controls, and legends now align closely with the public pages; moving graph nodes and optional failed public resources still require review. The staging service returned different availability lists and graph contents, so use production responses for public-page comparisons and recordings.

Rails calculates collaboration graphs for teams and two specialized organizations from Solr member records. Django now follows that separate path with bounded member batches and two levels of collaborators; tests check live/replay request equality, page rendering, CSV, and missing-recording failure using made-up records. These custom graphs still need a live Solr comparison. Organization pages now show the fixed decorative collaboration preview and link when `VIZ_ENABLED=true` and members are present. That preview comes from the reference template, not the visualization-service graph. A missing source setting or required recording returns 503.

The coauthor treemap reuses the coauthor graph response and Solr heading. Its tiles show publication counts by coauthor and link to that coauthor's treemap. A selected desktop comparison with the public page differed by about 0.15% of pixels, with optional failed public resources still reported separately. The page's CSV and JSON formats use the same graph data as the coauthor network page.

## Capture and replay one journey

With the source connection available, create a new directory outside Git:

```bash
uv run ./manage.py capture_solr_journey --query "$QUERY" --id "$PERSON_ID" --organization-id "$ORGANIZATION_ID" --output ../source_recordings/first-journey
```

The Django command calls the capture logic in [tools/source_capture.py](../tools/source_capture.py); neither runs while serving visitor requests. The command requires the chosen profile to appear in the first 20 unfiltered results. It then requests a People-filtered search, full facet values for both states, the profile, its affiliation records, and any supported CV PDF. When `--organization-id` is supplied, it also requests the organization, its member portraits, and the member records needed for its TSV. A configured active-team ID instead requests its member records and portraits. Add `--extra-search 'q=TERM&page=2'` up to four times to capture additional exact search states, including their full facets. Finally, it captures images named by the Solr documents. Omit `--organization-id` for a person-only journey. It reuses repeated responses and waits at least one second between distinct Solr requests. It stores unchanged response bytes and SHA-256 checksums in a format the existing recording reader validates. The capture is limited to 120 requests and 60 MB overall; Solr and images have a 3 MB per-response limit, and PDFs have a 10 MB limit. It refuses an existing output directory and any directory inside Git. If a request or write fails, files already written remain; the command writes the manifest last, so an incomplete directory cannot be selected for replay. The command makes no changes to upstream services.

Run the saved journey with the manifest path and replay mode:

```bash
PAGE_DATA_MODE=replay UPSTREAM_RECORDING_MANIFEST=../source_recordings/first-journey/manifest.json uv run ./manage.py runserver 127.0.0.1:8000
```

Replay requires an authentic recorded manifest. It matches the service, path, ordered repeated query values, and headers for each request. A missing or altered response fails; it cannot switch to the network, prepared pages, or samples. The local image and PDF routes also read recorded bytes. A supported PDF version redirect stays on the local route. Store real records, images, documents, and comparison output outside every Git checkout.

## Capture and replay visualization data

Set `VIZ_SERVICE_URL` to the production visualization root in the private environment file, then capture one person and optionally one ordinary organization into a new directory outside Git:

```bash
uv run ./manage.py capture_viz_journey --person-id "$PERSON_ID" --organization-id "$ORGANIZATION_ID" --output ../source_recordings/visualization
```

The command reads both graph-availability lists, the person's coauthor and collaborator responses, and the organization's collaborator response when supplied. It waits half a second between requests. It writes unchanged bodies and request keys, then reads those recordings through Django's normal replay path and checks that the parsed results match. Omit `--organization-id` for a person-only capture. Team and specialized-organization graphs use Solr records and are intentionally excluded from this visualization-service capture. The output directory must not already exist or be inside Git. If a request fails, no completed manifest is available for replay; any already written files remain in the new directory. This capture alone supplies graph inputs, not the Solr record needed to render a complete graph page.

## Compare the result

Use `tools/compare_sites.py` with an external case manifest as described in [the browser comparison guide](conversion/browser_comparison.md). Select matching search, profile, and organization URLs and the same browser viewport for both sites. The browser comparison checks status, selected text, images, and screenshots. It reports any changed pixels for review rather than treating a close visual match as accepted. Compare facet JSON by value and link query parameters, and compare a captured CV with the public PDF bytes. Keep the saved reference, local screenshots, and reports outside Git.

For a manual check, search for the captured term, select and remove the People filter, open the captured profile, follow its organization link, and return to search. Open the full facet values and CV link when present. The chosen search result must link to that profile. A second search term needs its own live request or recorded response; it must not reuse the first result.

## Current limits

This increment covers HTML search, person profiles, ordinary Solr-backed organizations, a selected active team, fixed-member and research-area organizations, search JSON, organization publication TSV, full facet JSON, supported CV PDFs, ordinary visualization graphs, coauthor treemaps, and organization publication and research charts. Nested profile JSON, graph CSV, and selected graph pages have public comparisons; network layout and browser downloads need further checks. A new exact organization chart and status recording ran through live processing and offline replay. Selected chart values matched saved public responses by meaning, though member order changes CSV bytes and chart colors. A selected custom team graph also ran through live processing and offline replay; its node identifiers, links, and CSV rows matched current public output. The public JSON still contains nested faculty objects on root nodes that Django omits, and one title differs. Desktop chart screenshots still need visual refinement. VIVO JSON-LD, Turtle, and RDF exports preserve backend bytes in local tests; live backend access remains unverified. The legacy image redirect is connected, but its live behavior needs checking. Source modes return 503 for unconverted handlers. The homepage book database and browser challenge remain source gaps. A CV link outside the configured document source remains an external link. Direct local service access does not prove access from the development server.

The parser converts common person fields, publications, education, appointments, teaching, affiliations, and outgoing links. It escapes source text before inserting it into page sections. Four additional public record shapes and their live Solr journeys were checked locally, including sparse profiles and one with many publications. No-results, later-page, and repeated-filter searches were also captured and replayed. The selected organization had 58 member rows with matching public text and images that all loaded; its source-backed page now includes the fixed visualization preview, but that change has not had a matched screenshot check. Other records and queries need matched checks. The public page can also fail optional analytics or status requests during a browser comparison; record those separately from core content and image differences.
