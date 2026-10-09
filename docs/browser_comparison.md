# Compare pages with saved references

The retained tool records observations and screenshots and reports differences. It was useful during conversion and may help verify future page changes. Manifests, captured pages, and reports stay outside every Git checkout.

## Contents

- [Prepare the browser and cases](#prepare-the-browser-and-cases)
- [Run a comparison](#run-a-comparison)
- [Read and review results](#read-and-review-results)
- [Reuse earlier comparisons carefully](#reuse-earlier-comparisons-carefully)

## Prepare the browser and cases

Install the optional local tools and browser:

```bash
uv sync --locked --group local
uv run playwright install chromium
```

These commands may download packages and Chromium. Alternatively pass --browser-executable with an existing compatible browser. Use the same browser/version for both sides.

Save a manifest outside Git. This example uses only local made-up addresses:

```json
{
  "reference_base_url": "http://127.0.0.1:8001",
  "local_base_url": "http://127.0.0.1:8000",
  "target_base_url": "http://127.0.0.1:8000",
  "cases": [{
    "id": "example-desktop",
    "path": "/",
    "width": 1440,
    "height": 900,
    "selectors": {"heading": "h1"},
    "actions": []
  }]
}
```

Choose exact paths and selectors for the pages being checked. Real addresses and records belong in the private manifest. Use a fresh empty output directory for each command.

## Run a comparison

From the checkout:

```bash
uv run -m tools.compare_sites self-test --output ../comparison-detector-check
uv run -m tools.compare_sites capture-reference --manifest ../comparison-cases.json --output ../comparison-reference
uv run -m tools.compare_sites compare-local --manifest ../comparison-cases.json --baseline ../comparison-reference --output ../comparison-local
uv run -m tools.compare_sites compare-target --manifest ../comparison-cases.json --baseline ../comparison-reference --output ../comparison-target
```

Self-test starts a small local test website and checks deliberate changes. Capture-reference visits selected reference pages, limits resource requests, pauses between pages, and writes a baseline. It performs form actions only when the manifest specifies them.

Compare-local reads the baseline and visits the selected local origin while blocking other origins. Compare-target visits the configured target and allows its ordinary external resources. Both write observations, screenshots, and reports. Follow the access already arranged for the site.

Use repeated --case options to select cases, or --failed-from with an earlier report to select cases that did not pass. These are alternative selection methods. Run --help for full arguments and action formats.

## Read and review results

Open report.html for side-by-side views, report.md for a short list, or report.json for structured results. The tool records status, content type, final address, title, selected text, images, resource/script failures, viewport, and browser version.

Changed pixels or observations require review and produce a nonzero result. Missing captures or failed resources cannot pass. The tool does not accept a small difference automatically. Inspect actual response headers and download bytes where the changed behavior requires them; detected encoding or a document's displayed media type is not the original full Content-Type.

For visual checks, inspect complete content through the footer at matching desktop/narrow sizes. Verify actual screenshot dimensions, loading state, and scroll coverage. Keep normal unmodified views alongside any focused comparison that hides changing content.

## Reuse earlier comparisons carefully

Reuse earlier results only when current code, assets, source content, layout conditions, fonts, and control states still match the inspected version. Record the revision and why those results still apply. Inspect all changed regions and keep partial views identified as partial.

Different URLs or states can share repeated content, but their unique navigation, controls, complete layout, downloads, and failures still need their own checks. These procedures support future changes; they do not resume the retired conversion batches.
