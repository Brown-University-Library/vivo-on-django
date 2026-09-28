# Source-backed search, profile, and organization journey

The live journey requests a Solr search, opens a person profile and an ordinary linked organization, and looks up member portraits in one additional Solr request. It also serves full search facet values and a supported profile CV PDF. Replay reads the same responses from an external manifest and runs the same page-building code without a network connection. Prepared mode remains the choice for the homepage and broader saved coverage.

## Contents

- [Configure a local source](#configure-a-local-source)
- [Capture and replay one journey](#capture-and-replay-one-journey)
- [Compare the result](#compare-the-result)
- [Current limits](#current-limits)

## Configure a local source

Set `SOLR_URL` to the Solr core or collection URL, including its final name. Set `IMAGES_URL` to the base address that serves profile images. Set `DOCUMENTS_URL` to the origin that serves profile CV PDFs if those links should pass through Django. Keep these values in the private environment file. A local SSH tunnel can supply Solr access while Django runs on the workstation; the tunnel must remain open for live requests. The source values in `example.env` are blank deliberately.

Use `PAGE_DATA_MODE=live` for live search, person profile, and ordinary organization requests. This mode reads the configured sources at request time. It does not require a prepared bundle. Django startup checks verify configuration without contacting the sources; a successful check alone does not establish connectivity. The supported HTML routes are `/search?q=...` and `/display/ID`; `/search_facets?f_name=FIELD&q=...` returns all values for one supported facet. Search accepts a page number and repeated `fq=FIELD|VALUE` filters for the four listed facets. An unsupported option returns 503 instead of sample content.

## Capture and replay one journey

With the source connection available, create a new directory outside Git:

```bash
uv run ./manage.py capture_solr_journey --query "$QUERY" --id "$PERSON_ID" --organization-id "$ORGANIZATION_ID" --output ../source_recordings/first-journey
```

The command requires the chosen profile to appear in the first 20 unfiltered results. It then requests a People-filtered search, full facet values for both states, the profile, its affiliation records, and any supported CV PDF. When `--organization-id` is supplied, it also requests that organization and its member portraits. Add `--extra-search 'q=TERM&page=2'` up to four times to capture additional exact search states, including their full facets. Finally, it captures images named by the Solr documents. Omit `--organization-id` for a person-only journey. It reuses repeated responses and waits at least one second between distinct Solr requests. It stores unchanged response bytes and SHA-256 checksums in a format the existing recording reader validates. The capture is limited to 120 requests and 60 MB overall; Solr and images have a 3 MB per-response limit, and PDFs have a 10 MB limit. It refuses an existing output directory and any directory inside Git. If a request or write fails, files already written remain; the command writes the manifest last, so an incomplete directory cannot be selected for replay. The command makes no changes to upstream services.

Run the saved journey with the manifest path and replay mode:

```bash
PAGE_DATA_MODE=replay UPSTREAM_RECORDING_MANIFEST=../source_recordings/first-journey/manifest.json uv run ./manage.py runserver 127.0.0.1:8000
```

Replay requires an authentic recorded manifest. It matches the service, path, ordered repeated query values, and headers for each request. A missing or altered response fails; it cannot switch to the network, prepared pages, or samples. The local image and PDF routes also read recorded bytes. A supported PDF version redirect stays on the local route. Store real records, images, documents, and comparison output outside every Git checkout.

## Compare the result

Use `tools/compare_sites.py` with an external case manifest as described in [the browser comparison guide](browser_comparison.md). Select matching search, profile, and organization URLs and the same browser viewport for both sites. The browser comparison checks status, selected text, images, and screenshots. It reports any changed pixels for review rather than treating a close visual match as accepted. Compare facet JSON by value and link query parameters, and compare a captured CV with the public PDF bytes. Keep the saved reference, local screenshots, and reports outside Git.

For a manual check, search for the captured term, select and remove the People filter, open the captured profile, follow its organization link, and return to search. Open the full facet values and CV link when present. The chosen search result must link to that profile. A second search term needs its own live request or recorded response; it must not reuse the first result.

## Current limits

This increment covers HTML search, person profiles, ordinary Solr-backed organizations, full facet JSON, and CV PDFs whose links match `DOCUMENTS_URL`. Other page families, structured formats, graph availability, visualizations, specialized organizations with custom members, and additional source services still need implementation. Source modes return 503 for unconverted handlers. A CV link outside the configured document source remains an external link. The local tunnel proves workstation access, not access from the development server.

The parser converts common person fields, publications, education, appointments, teaching, affiliations, and outgoing links. It escapes source text before inserting it into page sections. Four additional public record shapes and their live Solr journeys were checked locally, including sparse profiles and one with many publications. No-results, later-page, and repeated-filter searches were also captured and replayed. The selected organization had 58 member rows with matching public text and images that all loaded, but its source-backed page still lacks the public visualization preview. Other records and queries need matched checks. The public page can also fail optional analytics or status requests during a browser comparison; record those separately from core content and image differences.
