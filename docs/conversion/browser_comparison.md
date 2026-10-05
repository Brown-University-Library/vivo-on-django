# Compare saved reference pages with local pages

The command records selected browser observations and screenshots. All case manifests, captured pages, and reports must stay outside every Git checkout. Use saved prepared data for local checks; this command does not establish authentic source integration or complete site acceptance.

## Prepare and run

Run `uv sync --locked`, then `uv run playwright install chromium` to install the development dependencies and browser. Alternatively, pass `--browser-executable "$BROWSER_EXECUTABLE"` to use an existing Chromium executable. Use the same browser version for both captures. The command disables GPU rendering because Chrome otherwise gives slightly different pixels to the same JPEG when it loads from two site addresses. Capture a new reference before comparing screenshots made with an older version of this command.

Save a manifest such as this invented example outside Git:

```json
{
  "reference_base_url": "https://example.org",
  "local_base_url": "http://127.0.0.1:8000",
  "target_base_url": "https://restricted-django.example.org",
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
4. After installing Django on a restricted development server, run `uv run -m tools.compare_sites compare-target --manifest ../comparison-cases.json --baseline ../comparison-reference --output ../comparison-target`. This visits `target_base_url` and allows that page to load its normal outside resources. Keep the target address and generated evidence outside Git when they identify a real server.

Add `--case search-desktop` to compare one named case; repeat the option to choose several cases. Add `--failed-from ../earlier-comparison/report.json` to compare only cases that did not pass in an earlier report. Use one selection method at a time. The command prints the pass count, a short list of cases needing review, and the HTML report path.

Each output directory must be new or empty. Keep earlier reports when repeating a run. Cases can use `click`, `navigate`, `fill`, `hover`, `focus`, and `press` actions with a CSS `selector`; `value` supplies input or a key. Use `navigate` when a link loads another page: it waits for navigation and records that destination's HTTP response. Optional `wait_for` waits for another selector to become visible. Captures wait for fonts, images, and jQuery animations. Every selector in `selectors` must find at least one element; missing observations fail even when both sites lack that element.

A case can set `screenshot_css` when one changing visual detail hides the rest of a useful comparison. For example, `.hero { background-image: none !important; }` removes a randomly selected hero background from both captures while retaining the hero's size, text, and controls. Keep this CSS narrow. The copied manifest records the exact rule used for review.

## Read the results

For deployed comparisons, first follow [the automatic deployment procedure](../../WORKPLAN_STUFF/workplan.md#automatic-deployment-and-verification). Record the expected commit and the actual `response.loaded_version` from `/version/` through permitted access. Confirm actual served asset bytes; an updated checkout or asset query does not prove the browser has current CSS/JavaScript. Check the loaded revision again after each comparison group. Repeat observations affected by changed code, restarts, failed requests or interrupted interactions; automatic deployment can restart the application even at the same commit. Preserve existing access restrictions and do not extract authentication state into helpers.

Open `report.html` for side-by-side screenshots, `report.md` for a brief list, or `report.json` for structured results. Each case has observations, a screenshot, and an amplified pixel-difference image. The command records status, content type, final URL, title, selected visible text, image loading, resource failures, script errors, viewport, and browser version.

Any changed pixel or observation requires review and produces exit code 1. Missing screenshots, failed assets, script errors, blocked reference access, and incomplete captures cannot pass. Reference failures remain visible even when local pages load correctly. There is no automatic tolerance that accepts a visual difference.

For interactive browser captures, verify the selected tab after opening a linked document. Set its requested viewport after navigation and confirm the actual screenshot bitmap dimensions. Begin complete-page coverage at scroll position zero, record each subsequent scroll position, and continue through the footer with overlapping frames. Resizing can retain an earlier scroll position or affect another selected tab. A viewport setting or DOM size alone does not establish the screenshot size or complete coverage. Exclude incorrect captures and repeat them before counting visual checks as passed.

For animated dialogs, confirm the intended dialog's title, selected control and settled values before saving a result. Wait for the previous dialog to close before opening another. Preserve source-data differences separately from sorting or spacing results; a corrected control does not establish matching counts or whole-page completion.

## Current limits

This command now compares selected search, profile, organization, and homepage pages. It compares final URLs, but does not yet report every redirect hop or check all linked destinations, downloads, or JSON responses. A separate external check compares selected full redirect chains, response formats and cache headers, one saved cover image, and a CV download. A screenshot covers one viewport, not the entire page. Add explicit selectors and interaction cases for content below it. Use narrow `screenshot_css` for the homepage's changing background, then review the normal page separately to confirm that its background loads. The invented detector check proves selected failure detection; it does not prove that every real page has complete coverage.
