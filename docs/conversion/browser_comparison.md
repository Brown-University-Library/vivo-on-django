# Compare saved reference pages with local pages

The command records selected browser observations and screenshots. All case manifests, captured pages, and reports must stay outside every Git checkout. Use saved prepared data for local checks; this command does not establish authentic source integration or complete site acceptance.

Contents:

- [Prepare and run](#prepare-and-run)
- [Read the results](#read-the-results)
- [Read actual response headers and bodies](#read-actual-response-headers-and-bodies)
- [Repeated data and controls](#repeated-data-and-controls)
- [Reuse saved visual checks](#reuse-saved-visual-checks)
- [Current limits](#current-limits)

## Prepare and run

Current deployed comparisons use production Rails and production Django. Recover the private comparison bases and prepare current case bindings under Django’s `/vivo_on_django/` prefix; the local/prepared example below remains for offline checks. Preserve earlier staging check results and confirm that they still apply before reusing them.

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
4. After installing Django on a restricted development server, run `uv run -m tools.compare_sites compare-target --manifest ../comparison-cases.json --baseline ../comparison-reference --output ../comparison-target`. This visits `target_base_url` and allows that page to load its normal outside resources. Keep the target address and generated check results outside Git when they identify a real server.

Add `--case search-desktop` to compare one named case; repeat the option to choose several cases. Add `--failed-from ../earlier-comparison/report.json` to compare only cases that did not pass in an earlier report. Use one selection method at a time. The command prints the pass count, a short list of cases needing review, and the HTML report path.

Each output directory must be new or empty. Keep earlier reports when repeating a run. Cases can use `click`, `navigate`, `fill`, `hover`, `focus`, and `press` actions with a CSS `selector`; `value` supplies input or a key. Use `navigate` when a link loads another page: it waits for navigation and records that destination's HTTP response. Optional `wait_for` waits for another selector to become visible. Captures wait for fonts, images, and jQuery animations. Every selector in `selectors` must find at least one element; missing observations fail even when both sites lack that element.

A case can set `screenshot_css` when one changing visual detail hides the rest of a useful comparison. For example, `.hero { background-image: none !important; }` removes a randomly selected hero background from both captures while retaining the hero's size, text, and controls. Keep this CSS narrow. The copied manifest records the exact rule used for review.

## Read the results

For deployed comparisons, first follow [the automatic deployment procedure](../../WORKPLAN_STUFF/workplan.md#automatic-deployment-and-verification). Record the expected commit and the actual `response.loaded_version` from `/version/` through permitted access. Confirm actual served asset bytes; an updated checkout or asset query does not prove the browser has current CSS/JavaScript. Check the loaded revision again after each comparison group. Repeat observations affected by changed code, restarts, failed requests or interrupted interactions; automatic deployment can restart the application even at the same commit. Preserve existing access restrictions and do not extract authentication state into helpers.

Open `report.html` for side-by-side screenshots, `report.md` for a brief list, or `report.json` for structured results. Each case has observations, a screenshot, and an amplified pixel-difference image. The command records status, content type, final URL, title, selected visible text, image loading, resource failures, script errors, viewport, and browser version.

Any changed pixel or observation requires review and produces exit code 1. Missing screenshots, failed assets, script errors, blocked reference access, and incomplete captures cannot pass. Reference failures remain visible even when local pages load correctly. There is no automatic tolerance that accepts a visual difference. Follow [the thirty-minute investigation limit](../../WORKPLAN_STUFF/workplan.md#limit-unexplained-rendering-investigations) across case revisits, including capture-method diagnosis. At the limit, preserve the check results, prepare one review under [optional owner comparison reviews](../../WORKPLAN_STUFF/workplan.md#optional-owner-comparison-reviews) and continue independent work. A precisely scoped owner acceptance belongs in [accepted_differences.md](../../WORKPLAN_STUFF/accepted_differences.md); other required checks remain.

For new interactive comparison tabs, set the requested viewport on the blank tab before loading the page. After opening a linked document, verify the selected tab and its actual viewport and screenshot bitmap dimensions. When taking a new complete-page capture, begin at scroll position zero, record each subsequent scroll position, and continue through the footer with overlapping frames. Resizing can retain an earlier scroll position or affect another selected tab. A viewport setting or DOM size alone does not establish the screenshot size or complete coverage. Exclude incorrect captures and repeat them before counting visual checks as passed. Use the procedure below when complete applicable check results already exist; a saved capture without visual review is not a pass.

Use the same capture method and selected-tab conditions for both pages. Preserve original image files and their embedded color profiles. A browser capture can omit the monitor profile while a native window capture retains it; comparing their raw colors can create an apparent difference. Convert both original profiles to the same color space when needed and record the conversion and observed viewport position. Keep unexplained image pixels Pending even when complete image files and computed styles agree. Confirm that animated carousel items have finished moving and that the intended group is still visible; automatic advancement can hide a previously selected cover before capture.

When measuring page movement, inspect the scrolling element actually used by the page. Some retained layouts scroll the body while `window.scrollY` and the document root remain zero. Record body movement and the footer position too; require complete footer coverage and exclude repeated frames. Responsive headers can change height during scrolling; retain that state instead of treating it as unexplained page loss.

For animated dialogs, confirm the intended dialog's title, selected control and settled values before saving a result. Wait for the previous dialog to close before opening another. Preserve source-data differences separately from sorting or spacing results; a corrected control does not establish matching counts or whole-page completion.

Complete each native download Save dialog before starting another browser check. Explicitly choose the current run's private check records folder and a filename identifying the reference or target artifact; browsers can retain a previous run's folder. Confirm that the dialog closes and the file exists before continuing. A pending Save dialog can obstruct other content and leave a download check waiting; inspect it before treating a download timeout as a failure.

## Read actual response headers and bodies

When ordinary page navigation works but an HTTP helper cannot use browser sign-in, Codex can inspect the request the page already makes through the browser’s Network panel. Preserve existing access restrictions; this does not authorize an alternate request to a rejected destination.

1. Select the intended tab and confirm its address before opening developer tools. Use its Network panel and filter to identify the document or supporting request.
2. Reload the permitted page or activate its ordinary offered control. Confirm the selected row belongs to that action.
3. Read the General status and required response-header values. Keep request headers collapsed. Do not copy request headers, authentication values, a request command or a network archive.
4. For an allowed response-body comparison, select Response and inspect its actual text. A displayed code editor can expose only part of a response. Use ordinary scrolling if needed; verify that the full response parses and its recorded byte count agrees with the resource size before claiming complete-body equality.
5. Save only the required response values and check results privately. An empty clipboard, truncated editor, document media type or detected encoding does not prove the original response bytes or full Content-Type.
6. Close developer tools and restore the required viewport before taking comparison captures. Confirm the bitmap size and the settled page state. A capture can alter scrollbars or scroll position; record that change and compare under matching conditions rather than treating it as an application difference.

## Repeated data and controls

Follow [the workplan procedure](../../WORKPLAN_STUFF/workplan.md#check-repeated-data-and-controls-efficiently) and record the affected check revisions under [RC01](../../WORKPLAN_STUFF/completion_checks.md#approved-procedure-for-repeated-checks) before replacing exhaustive repeated checks. Preserve original definitions and valid earlier check results. Compare complete current arrays, values, ordering and destination addresses using supported tools; a few screenshots cannot establish complete-data equality.

For equivalent repeated dialogs, lists or carousel groups, record first, middle and last examples for each offered sort order at both widths. Include short final groups, longest labels, disabled boundaries and different markup. Check the applicable controls, filtering, selection/removal, empty-result recovery, keyboard/pointer use, Escape/focus return and carousel pause/resume. Compare all destination addresses, then exercise representative real journeys for each distinct destination behavior. Preserve specifically configured original journeys and unresolved named checks. Expand coverage when an example differs or uses different code or layout.

Inspect every required endpoint and distinct layout/state through its footer at both widths. Selected examples replace repeated inspection of equivalent groups; they do not replace unique pages, required responses, complete artifacts, resources, accessibility or deployed verification. Record remaining gaps and unexplained pixels. Apply the investigation limit and [optional owner-review queue](../../WORKPLAN_STUFF/workplan.md#optional-owner-comparison-reviews); preparation or silence accepts no difference. Use existing check results and tools rather than delaying case work to build a new helper.

## Reuse saved visual checks

Every required endpoint and variation still needs a recorded visual comparison. The steps below reduce repeated review of content already inspected; they do not replace an endpoint's visual check with a representative page or a successful text comparison. Preserve existing check IDs and original passing conditions. Record any approved RC01 revision under [repeated checks](#repeated-data-and-controls); individual accepted differences follow the owner-decision procedure.

1. **Recover the case's completed check results first.** List the required views and checks, their comparison record labels, comparison dates and loaded revisions. Identify unfinished or invalid observations. Keep completed captures and inspections after a pause or a documentation-only release when application code, served assets, source content and comparison conditions remain applicable. Correct only the excluded or incomplete observations. A stored file or an earlier partial view alone cannot establish a pass.
2. **Check applicability before reuse.** Confirm the viewport and rendering conditions, visible content and order, inline markup, loaded images/fonts, relevant styles, rendered dimensions and wrapping, and active control state. Check current source data and whether changed code or assets affect the observation. Use the supported browser tools; collect related measurements together when possible. Recheck the loaded revision before and after the comparison group. If the tools cannot establish applicability, or a restart interrupts the observation, take fresh screenshots and record new observations for the affected area.
3. **Review a repeated view for its own layout and behavior.** For a profile's View All state at each width, directly inspect the header, selected control, section order and visibility, each section boundary, combined spacing and footer. Confirm the complete rendered view through the footer. Interior section check results may be reused only when current observations establish that the section's content, styling, local geometry and wrapping agree with the inspected individual-section view on both sites. Ancestor styles, responsive headers, changed widths, hidden rows or additional content can invalidate that reuse. Inspect all new or different regions. When equivalence is uncertain, capture and inspect the complete affected section or view.
4. **Avoid opening the same saved visual checks repeatedly.** An exactly identical image region can refer to an already visually inspected image under matching conditions. Inspect any newly encountered pixel difference; matching text or an image hash alone does not explain a changed layout. Keep raw captures and differences. Do not mask required content or widen tolerances to turn a difference into a pass. Different images and pointer states need their existing explanation or new review.
5. **Record how the complete view was checked.** For each visual check, record the state and viewport, directly inspected areas, reused comparison record labels and their revisions, current observations establishing applicability, and any remaining gap or difference. Every required region through the footer must be accounted for by direct inspection or applicable visually inspected check results. Missing coverage stays partial or pending. Downloads still require their own document bytes, rendered pages and applicable delivery checks; shared checks follow [the workplan](../../WORKPLAN_STUFF/workplan.md#handle-shared-differences-once).

On resumption, apply this procedure to unfinished checks without restarting valid completed work. For the next two profile audits, note approximate elapsed audit time and captured frame count in the existing private result records, alongside complete-view results and remaining gaps. Use comparable page lengths and states when judging whether effort decreased. This adds no new passing condition or scheduled report. Reuse supported capture routines when available; this workflow change does not require creating a new helper before continuing.

## Current limits

This command now compares selected search, profile, organization, and homepage pages. It compares final URLs, but does not yet report every redirect hop or check all linked destinations, downloads, or JSON responses. A separate external check compares selected full redirect chains, response formats and cache headers, one saved cover image, and a CV download. A screenshot covers one viewport, not the entire page. Add explicit selectors and interaction cases for content below it. Use narrow `screenshot_css` for the homepage's changing background, then review the normal page separately to confirm that its background loads. The invented detector check proves selected failure detection; it does not prove that every real page has complete coverage.
