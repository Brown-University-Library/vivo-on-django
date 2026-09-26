# Prepared data for local pages

Prepared mode reads a separately distributed bundle and renders saved searches and profiles without contacting services. It also serves saved supporting responses and images. This supports local page and interaction development; it does not verify Solr processing, live integration, or visual agreement with the reference site.

## Contents

- [Local setup](#local-setup)
- [Bundle format](#bundle-format)
- [Page fields](#page-fields)
- [Validation and failures](#validation-and-failures)
- [Current limits](#current-limits)

## Local setup

Install the locked dependencies and prepare the local directories and database using the repository README. Unpack a compatible bundle beside the checkout as `../prepared_fixture_data/`. Keep real data outside every Git checkout.

Set these values in local environment configuration, or supply them for an individual command:

```dotenv
PAGE_DATA_MODE=prepared
PREPARED_FIXTURE_DIR=../prepared_fixture_data
```

Relative bundle paths resolve against the Django project root. No original workstation paths are required.

```bash
uv run ./manage.py validate_prepared_data
PAGE_DATA_MODE=prepared uv run ./manage.py runserver 127.0.0.1:8000
```

The validator reads every listed page, supporting response, image, font, and README. It checks required fields, request states, case references, relative paths, and SHA-256 checksums. It prints aggregate JSON including data origin and explicit unverified integration and visual results. `--case CASE_ID` additionally requires a listed case; it does not skip validation of the rest of the bundle. The command never contacts a service and changes no bundle data.

Use a search URL listed in the bundle's manifest. The homepage and other unconverted public handlers return 503 in prepared mode. Use the bundle README for its supported journey and limitations.

`PAGE_DATA_MODE` defaults to `prototype` to retain the existing sample site when no source is selected. This is a temporary, explicitly reported mode. `prepared` requires a valid external bundle. `replay` and `live` fail startup checks because page processing for those modes is not implemented. Unknown modes fail too. A missing prepared state never switches modes.

## Bundle format

Format version 1 uses `manifest.json`, a README, page JSON under `data/`, and assets under `assets/`. Supporting response files may use other extensions. Manifest fields:

| Field | Meaning |
| --- | --- |
| `format_version` | Integer `1`; the loader rejects unsupported versions. |
| `bundle_version` | A release name made from letters, numbers, dots, underscores, or hyphens. |
| `application_revision` | Compatible application revision or working revision description. This is recorded information; format and field validation determine whether the loader can read the bundle. |
| `data_origin` | `invented` or `prepared_from_reference`. Neither denotes authentic upstream replay. |
| `prepared_at` | ISO timestamp including its timezone. |
| `readme` | Object with relative `file` and `sha256`. |
| `assets` | Map from simple asset filenames to relative `file`, `sha256`, and `content_type`. |
| `entries` | Map from unique entry names to exact saved requests and files. |
| `cases` | Map from case names to nonempty lists of entry names. Every entry must belong to a case. |

Each entry declares `family` (`search`, `profile`, or `response`), a site-relative `path`, decoded `query` pairs, a relative `file`, and `sha256`. Repeated query keys use repeated pairs, for example `[["q", "Example"], ["fq", "record_type|PEOPLE"], ["fq", "affiliations|Example Unit"]]`.

Parameter names may appear in a different order. Values under a repeated name retain their order and meaning. A single `page=1` and an omitted page select the same state. Paths with and without a final slash select the same prepared entry; both search and profile forms are routed directly. Other differences require another saved state.

A `response` entry also declares `status`, `content_type`, and optional `headers` as string pairs. Its original body bytes are returned unchanged. Supported headers are Content-Disposition, Location, and Cache-Control. Search JSON, profile JSON, and facet JSON require their own saved entries; they are not synthesized from HTML page fields. Other download and representation handlers are not connected yet.

Asset URLs use `/__prepared_assets/ASSET_NAME`. Only listed assets are served; missing names return 404. Images and fonts must use supported content types. HTML bundles include `source-sans-pro.ttf`; the application supplies its own styles, scripts, and icon font. The icon font comes from the existing Rails asset set.

## Page fields

Search data supplies `query`, integer `page`, `page_size`, `total`, and ordered `results`. Every result has `id`, `name`, `title`, `email`, site-relative `url`, and bundled `thumbnail`. Empty text is permitted where the source has no value. The template derives the displayed range from page number, size, and total.

`facets` contains objects with `name`, `title`, and `values`. Each value has `text`, integer `count`, site-relative `url`, and boolean `selected`. `selected_filters` contains `label` and removal `url`. `pagination` contains `label`, `url`, and optional boolean `current`. `previous_url`, `next_url`, and `remove_query_url` are site-relative URLs or empty strings. Store explicit supported combinations, including their own counts and result order. The reader does not calculate search results or facets.

Profile data supplies explicit `id`, `name`, `title`, bundled `thumbnail`, and ordered `sections`. Sections contain `id`, `label`, and `html`. Supported section IDs are Overview, Publications, Research, Background, Affiliations, and Teaching. Overview must come first; absent optional sections have no entry. Rich text permits ordinary formatted content and links, rejects executable elements and inline event handlers, and requires local images.

Both page families use the ordinary application templates. Profile navigation supports section fragments, reload, View All, and returning to the last successfully rendered search URL in the session. Rich content does not implement publication filtering or other removed source-page controls.

## Validation and failures

Django startup checks report the selected mode, bundle version, origin, and case count. They reject missing or invalid data. Unsupported prepared requests return 503 with a concrete explanation; they do not return sample records. Template errors remain errors instead of becoming successful placeholder responses.

Bundles load once per process. Restart Django after selecting a new version. The process continues using already validated bytes if files change while it runs. Create a new version when distributing changes; do not overwrite a shared release silently.

Prepared and replay responses restrict automatic browser resources to the local origin. Prepared pages omit remote analytics and load their text font locally. External links remain links that a user may choose to follow.

Repository tests use temporary invented bundles and block socket connections during the selected journey. Real bundle evidence and browser reports remain outside Git. Copy the working checkout and bundle to a separate directory and validate there before distributing them.

## Current limits

The first external bundle covers selected search pagination, filter combinations and removals, an empty-result state, six profiles with optional sections, and three facet responses. It does not include every destination linked from those pages. Consult its manifest for exact requests and its README for evidence dates and limitations.

Profile section markup and search layout are initial connections for presentation work. Complete publication controls, more-facet controls, homepage data, remaining endpoints, exact visual comparisons, authentic service response processing, and replay/live integration remain unfinished. The existing raw-response reader remains separate from prepared page data.
