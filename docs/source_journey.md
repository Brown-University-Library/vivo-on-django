# First source-backed search and profile journey

The first live journey requests a Solr search, opens a person profile, looks up affiliation images in Solr, and serves portraits and logos from the configured image source. Replay reads the same responses from an external manifest and runs the same page-building code without a network connection. The existing search and profile templates render both modes. Prepared mode remains the choice for the homepage and broader saved coverage.

## Contents

- [Configure a local source](#configure-a-local-source)
- [Capture and replay one journey](#capture-and-replay-one-journey)
- [Compare the result](#compare-the-result)
- [Current limits](#current-limits)

## Configure a local source

Set `SOLR_URL` to the Solr core or collection URL, including its final name. Set `IMAGES_URL` to the base address that serves profile images. Keep both values in the private environment file. A local SSH tunnel can supply Solr access while Django runs on the workstation; the tunnel must remain open for live requests. The source values in `example.env` are blank deliberately.

Use `PAGE_DATA_MODE=live` for live search and person profile requests. This mode reads the configured sources at request time. It does not require a prepared bundle. Django startup checks verify configuration without contacting the sources; a successful check alone does not establish connectivity. The initial live HTML routes are `/search?q=...` and `/display/ID`. Search accepts a page number and repeated `fq=FIELD|VALUE` filters for the four listed facets. An unsupported option returns 503 instead of sample content.

## Capture and replay one journey

With the source connection available, create a new directory outside Git:

```bash
uv run ./manage.py capture_solr_journey --query "$QUERY" --id "$PERSON_ID" --output ../source_recordings/first-journey
```

The command requires the chosen profile to appear in the first 20 unfiltered results. It then requests a People-filtered search, the profile, any affiliation records needed for logos, and the images named by those records. It stores unchanged response bytes and SHA-256 checksums in a format the existing recording reader validates. The capture is limited to 24 requests, 3 MB per response, and 25 MB overall. It refuses an existing output directory and any directory inside Git. If a request or write fails, files already written remain; the command writes the manifest last, so an incomplete directory cannot be selected for replay. The command makes no changes to upstream services.

Run the saved journey with the manifest path and replay mode:

```bash
PAGE_DATA_MODE=replay UPSTREAM_RECORDING_MANIFEST=../source_recordings/first-journey/manifest.json uv run ./manage.py runserver 127.0.0.1:8000
```

Replay requires an authentic recorded manifest. It matches the service, path, ordered repeated query values, and headers for each request. A missing or altered response fails; it cannot switch to the network, prepared pages, or samples. The local image route also reads the recorded image bytes. Store real records, images, and comparison output outside every Git checkout.

## Compare the result

Use `tools/compare_sites.py` with an external case manifest as described in [the browser comparison guide](browser_comparison.md). Select the matching search and profile URLs and the same browser viewport for both sites. The browser comparison checks status, selected text, images, and screenshots. It reports any changed pixels for review rather than treating a close visual match as accepted. Keep the saved reference, local screenshots, and reports outside Git.

For a manual check, search for the captured term, select and remove the People filter, open the captured profile, and return to search. The chosen search result must link to that profile. A second search term needs its own live request or recorded response; it must not reuse the first result.

## Current limits

This is an HTML search-to-person-profile increment. Other page families, structured formats, full facet lists, CV downloads through Django, graph availability, and additional source services still need implementation. Source modes return 503 for unconverted handlers. A profile's CV link currently leads to its public source URL when present. Search result links for organizations also need their source-backed display pages before those journeys are complete. The local tunnel proves workstation access, not access from the development server.

The parser currently converts common person fields, publications, education, appointments, teaching, affiliations, and outgoing links. It escapes source text before inserting it into page sections. More varied profiles need matched cases and additional conversion rules. The public page can also fail optional analytics or status requests during a browser comparison; record those separately from core content and image differences.
