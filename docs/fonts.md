# Fonts used by public pages

Matching the reference site's fonts is part of the existing appearance requirement. Differences in font files, character coverage, weight, style, or browser drawing need investigation; they are not accepted merely because they are small.

The shared public template loads `static/css/fonts.css` across the public page data modes. The stylesheet uses unmodified Source Sans Pro 2.045 WOFF2 files from the reference site's Google Fonts stylesheet. Its seven character ranges cover Latin, extended Latin, Greek, extended Greek, Cyrillic, extended Cyrillic, and Vietnamese. Each file lives under `static/fonts/` in `vivo_app/`. The original copyright notice and SIL Open Font License are in `static/fonts/SOURCE-SANS-LICENSE.txt`.

The reference stylesheet declares only normal style and weight 400. Keep those declarations and the original character ranges. The browser produces the requested bold and italic forms from that face, as it does on the reference site. Adding separate bold files or substituting Source Sans 3 would change that behavior. Existing Helvetica, Arial, and monospace fallback lists remain unchanged; comparisons must use the same browser and operating system.

Bootstrap uses the existing local Glyphicons Halflings WOFF2 file. The conversion checked its bytes against the reference Bootstrap 3.3.6 asset and the Source Sans Pro files against their originals. No font request needs Google Fonts or a prepared-data asset at runtime. Older prepared bundles may still contain the unused TTF; those bundles remain compatible and unchanged.

Font sources: [Google Fonts stylesheet](https://fonts.googleapis.com/css?family=Source+Sans+Pro), [Adobe Source Sans](https://github.com/adobe-fonts/source-sans), and [Bootstrap 3.3.6 icon font](https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/fonts/glyphicons-halflings-regular.woff2). Recheck the reference stylesheet before updating these files; a newer release is not automatically a closer match.

Run `uv run ./run_tests.py vivo_app.tests.test_fonts -v` to check shared template selection and local delivery of all eight WOFF2 assets. These checks do not replace browser comparisons of normal, bold, italic, and accented text. Keep detailed font captures and visual reports outside Git.
