# Homepage and organization comparison findings

These findings use the saved public-site baseline, prepared bundle `2026.09.27.3`, and the same Chrome version for each side of a comparison. The comparison reports still mark known public analytics failures and intentionally unloaded carousel images for review.

## Organization page

The narrow organization page matched pixel for pixel. At 1440 pixels wide, 5,659 pixels differed, or about 0.39 percent of the screenshot. The difference was limited to the bold organization heading and the bold visualization-button text. The page structure, normal-weight text, images, graph, spacing, and saved observations matched.

Browser inspection reported the same family, weight, size, width, and height for the affected elements. The public page receives the regular Source Sans Pro file as WOFF2. Prepared mode serves a TTF containing the same font version and the same character widths. This evidence points to Chrome drawing the synthesized bold edges slightly differently for those two file formats.

Matching the font files is required by the existing appearance goal. On September 28, 2026, the application replaced the prepared TTF declaration with the exact reference WOFF2 files and character ranges, served as application static assets. Both prototype and prepared pages now use those files. The icon font already matched byte for byte. See [the font notes](fonts.md) for sources and behavior. Existing prepared bundles remain unchanged; the font update is tracked with application code. The older screenshot counts above describe the TTF implementation and must not be treated as an accepted difference.

## Homepage

The randomly selected hero photograph accounted for the large earlier difference. A focused comparison used `screenshot_css` to remove only that background. The hero size, logo, search form, link, colors, and spacing then matched exactly.

The only remaining screenshot pixels were in the first two visible book covers. The public and saved copies of both files had identical SHA-256 hashes and natural dimensions. Hiding the cover pixels while preserving each image's size produced a zero-pixel layout difference. The normal screenshot should still be reviewed to confirm that a background and the first four covers load.

The image observations also found one useful text difference: Django called the small visualization picture “Visualization icon,” while the public page called it “A clip art visualization of a simple network.” The Django template now uses the public page's more descriptive text.

## How to repeat the focused checks

Use `.hero { background-image: none !important; }` as a homepage case's `screenshot_css` when comparing the stable hero layout. If cover-image drawing obscures a layout check, add `#books-carousel img { visibility: hidden !important; }` and verify the cover files separately by hash and dimensions. Keep an ordinary unmodified screenshot beside these focused checks so changing content is still visible to the reviewer.

The browser comparison command copies the manifest into each output directory. That preserves the exact CSS used and prevents a focused screenshot from being mistaken for a normal page capture.

A follow-up desktop check also found that the organization template omitted the spacing contributed by empty paragraphs around the reference website links. The local stylesheet now preserves that spacing without adding empty markup; its narrow-screen rule remains unchanged. The font assets match the reference bytes, but the old comparison reports have not been rewritten or reclassified as passing. Full visual acceptance still requires the agreed comparison coverage.
