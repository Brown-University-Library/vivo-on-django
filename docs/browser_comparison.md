# Compare saved reference pages with local pages

The command records selected browser observations and screenshots. All case manifests, captured pages, and reports must stay outside every Git checkout. Use saved prepared data for local checks; this command does not establish authentic source integration or complete site acceptance.

## Prepare and run

Run `uv sync --locked`, then `uv run playwright install chromium` to install the development dependencies and browser. Alternatively, pass `--browser-executable "$BROWSER_EXECUTABLE"` to use an existing Chromium executable. Use the same browser version for both captures.

Save a manifest such as this invented example outside Git:

```json
{
  "reference_base_url": "https://example.org",
  "local_base_url": "http://127.0.0.1:8000",
  "data_mode": "prepared",
  "bundle_version": "example-1",
  "cases": [{
    "id": "search-desktop",
    "path": "/search?q=Example",
    "width": 1440,
    "height": 1000,
    "selectors": {"range": ".search-result-numbers"},
    "actions": []
  }]
}
```

1. Run `uv run -m tools.compare_sites self-test --output ../comparison-detector-check`. This starts a temporary local test website and checks that unchanged pages match and deliberate heading, redirect, content-type, missing-image, and layout changes are detected. It also checks missing required elements and a changed HTTP status after following a link. It does not contact a public site.
2. Run `uv run -m tools.compare_sites capture-reference --manifest ../comparison-cases.json --output ../comparison-reference`. This visits the selected public pages and saves a baseline. It limits each case to 150 requests and pauses between pages. It does not submit forms unless the manifest explicitly instructs a browser action.
3. Start Django using the chosen prepared bundle. Run `uv run -m tools.compare_sites compare-local --manifest ../comparison-cases.json --baseline ../comparison-reference --output ../comparison-local`. This visits only the chosen loopback origin and blocks requests elsewhere. It reads the baseline without changing it.

Each output directory must be new or empty. Keep earlier reports when repeating a run. Cases can use `click`, `navigate`, `fill`, `hover`, `focus`, and `press` actions with a CSS `selector`; `value` supplies input or a key. Use `navigate` when a link loads another page: it waits for navigation and records that destination's HTTP response. Optional `wait_for` waits for another selector to become visible. Captures wait for fonts, images, and jQuery animations. Every selector in `selectors` must find at least one element; missing observations fail even when both sites lack that element.

## Read the results

Open `report.html` for side-by-side screenshots, `report.md` for a brief list, or `report.json` for structured results. Each case has observations, a screenshot, and an amplified pixel-difference image. The command records status, content type, final URL, title, selected visible text, image loading, resource failures, script errors, viewport, and browser version.

Any changed pixel or observation requires review and produces exit code 1. Missing screenshots, failed assets, script errors, blocked reference access, and incomplete captures cannot pass. Reference failures remain visible even when local pages load correctly. There is no automatic tolerance that accepts a visual difference.

## Current limits

This command now compares selected search, profile, organization, and homepage pages. It compares final URLs, but does not yet report every redirect hop or check all linked destinations, downloads, or JSON responses. A separate external check compares selected full redirect chains, response formats and cache headers, one saved cover image, and a CV download. A screenshot covers one viewport, not the entire page. Add explicit selectors and interaction cases for content below it. Homepage backgrounds change on each load, so their screenshots need direct review. The invented detector check proves selected failure detection; it does not prove that every real page has complete coverage.
