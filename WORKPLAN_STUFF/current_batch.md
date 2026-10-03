# Current batch and URLs being evaluated

Follow [workplan.md](workplan.md). Exact Rails and Django URLs are in `../../current_urls.local.md`, outside the repository. Detailed evidence uses private label `batch-001-profile-checks`.

Contents:

- [Batch status](#batch-status)
- [Current URL cases](#current-url-cases)
- [Changes in this batch](#changes-in-this-batch)
- [Local validation](#local-validation)
- [Handoff and evaluation](#handoff-and-evaluation)

## Batch status

- Batch ID: batch-001.
- State: application changes pushed; awaiting owner deployment.
- Started / last updated: October 3, 2026.
- Goal: correct person-profile citations and complete related profile navigation and section display.
- Branch / starting revision: `main` / `4a50060`.
- Planned change count: 30.
- Completed local changes: 30. Deployed checks: 0; pending owner deployment.
- Application commit / pushed revision: `9b9b739` (`Improves profile citations and navigation`), confirmed pushed to `main` on October 3, 2026. Batch records accompany this commit on the same branch.
- Owner deployment confirmation: pending.
- Loaded deployed revision: not checked for this batch.
- Next responsible person and action: the owner deploys the pushed `main` branch and confirms completion. Codex then verifies the loaded revision and compares the selected URLs.

The prior prompt archive records the previous implementation revision as loaded before this workflow began. No previous batch is awaiting deployment in these records. Existing local milestones do not establish deployed URL completion. Rails source and saved upstream/public evidence identify the differences in this batch; no current deployed pass is claimed.

## Current URL cases

| Pending ID / case ID | Safe URL pattern and variation | Expected Rails behavior | Required post-deployment comparison | Result / evidence label / next action |
| --- | --- | --- | --- | --- |
| S07 / P01 | `/display/{person_id}` with publications and profile sections | Preserve citation text, punctuation, links, and section navigation. | Compare all visible publications and sections at desktop/narrow widths, including search return. | Not evaluated after deployment; finish this URL before expanding to another family. |
| S07 / P04 | `/display/{person_id}` with additional citation/section variations | Preserve the same rules across differing source content. | Exercise applicable variations not present on the primary URL. | Regression and variation check pending. |
| S07 / P07 | `/display/{person_id}` with conditional section content | Preserve controls and visibility without inventing absent sections. | Exercise available tabs, View All, and linked supporting pages. | Regression and variation check pending. |

Use these cases in order. A passing primary URL does not establish that every profile variation passes. If a source variation needed for an individual change is absent, record that change as checked locally only and leave its deployed demonstration pending. Do not edit live records merely to create a test case.

## Changes in this batch

| Change ID | Case IDs | Observed difference and intended result | Local check and result | Commit | Deployed check and result | Remaining difference / next action |
| --- | --- | --- | --- | --- | --- | --- |
| batch-001-01 | P01; P04/P07 for additional variations | Avoid repeated periods after article page numbers. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Compare an article whose pages already end in a period. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-02 | P01; P04/P07 for additional variations | Avoid repeated periods after chapter page numbers. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Compare a chapter whose pages already end in a period. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-03 | P01; P04/P07 for additional variations | Avoid repeated volume separators. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Compare a volume already ending in a comma. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-04 | P01; P04/P07 for additional variations | Avoid repeated issue separators. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Compare an issue already ending in a comma. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-05 | P01; P04/P07 for additional variations | Avoid repeated editor separators. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Compare chapter editor text already ending in a comma. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-06 | P01; P04/P07 for additional variations | Avoid repeated publisher separators. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Compare publisher text already ending in a comma. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-07 | P01; P04/P07 for additional variations | Avoid repeated location separators. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Compare publication location text already ending in a comma. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-08 | P01; P04/P07 for additional variations | Preserve nested quotation marks in chapter titles. | `test_source_title_and_author_punctuation_is_preserved`: passed. | `9b9b739` | Compare a chapter title with nested quotation marks. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-09 | P01; P04/P07 for additional variations | Preserve author ellipses. | `test_source_title_and_author_punctuation_is_preserved`: passed. | `9b9b739` | Compare authors whose text already ends in multiple periods. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-10 | P01; P04/P07 for additional variations | Preserve title ending punctuation. | `test_source_title_and_author_punctuation_is_preserved`: passed. | `9b9b739` | Compare quoted titles already ending in multiple periods. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-11 | P01; P04/P07 for additional variations | Preserve quotation marks in italic book titles. | `test_source_title_and_author_punctuation_is_preserved`: passed. | `9b9b739` | Compare a book with supplied title quotation marks. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-12 | P01; P04/P07 for additional variations | Render italic text in publication titles. | `test_scientific_title_formatting_and_entities_render_as_text`: passed. | `9b9b739` | Compare a citation with italic words rather than literal markup. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-13 | P01; P04/P07 for additional variations | Render subscripts in publication titles. | `test_scientific_title_formatting_and_entities_render_as_text`: passed. | `9b9b739` | Compare a citation with a subscript. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-14 | P01; P04/P07 for additional variations | Render superscripts in publication titles. | `test_scientific_title_formatting_and_entities_render_as_text`: passed. | `9b9b739` | Compare a citation with a superscript. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-15 | P01; P04/P07 for additional variations | Display numeric publication volumes. | `test_numeric_metadata_and_blank_journal_fallback`: passed. | `9b9b739` | Compare a numeric-volume source variation when available. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-16 | P01; P04/P07 for additional variations | Display numeric publication issues. | `test_numeric_metadata_and_blank_journal_fallback`: passed. | `9b9b739` | Compare a numeric-issue source variation when available. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-17 | P01; P04/P07 for additional variations | Display numeric publication pages. | `test_numeric_metadata_and_blank_journal_fallback`: passed. | `9b9b739` | Compare a numeric-pages source variation when available. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-18 | P01; P04/P07 for additional variations | Trim surrounding spaces from DOI links. | `test_padded_citation_links_reach_the_intended_destination`: passed. | `9b9b739` | Open a DOI from a source value with surrounding spaces. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-19 | P01; P04/P07 for additional variations | Trim surrounding spaces from PubMed identifiers. | `test_padded_citation_links_reach_the_intended_destination`: passed. | `9b9b739` | Open a PubMed link from a source value with surrounding spaces. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-20 | P01; P04/P07 for additional variations | Trim surrounding spaces from citation website links. | `test_padded_citation_links_reach_the_intended_destination`: passed. | `9b9b739` | Open a citation website from a source value with surrounding spaces. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-21 | P01; P04/P07 for additional variations | Use the venue when the journal field is blank. | `test_numeric_metadata_and_blank_journal_fallback`: passed. | `9b9b739` | Compare a citation with a whitespace-only journal and a valid venue. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-22 | P01; P04/P07 for additional variations | Display encoded ampersands as citation text. | `test_scientific_title_formatting_and_entities_render_as_text`: passed. | `9b9b739` | Compare a citation title containing an encoded ampersand. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-23 | P01; P04/P07 for additional variations | Display encoded apostrophes as citation text. | `test_scientific_title_formatting_and_entities_render_as_text`: passed. | `9b9b739` | Compare a citation title containing an encoded apostrophe. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-24 | P01; P04/P07 for additional variations | Show inactive profile status on narrow screens. | Initial template test and desktop/narrow browser checks: passed. | `9b9b739` | Compare an inactive profile at desktop and narrow widths. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-25 | P01; P04/P07 for additional variations | Reset stale search-return links on direct visits. | Direct-entry regression, prepared-page test, and browser check: passed. | `9b9b739` | Visit a profile directly after an unrelated search; Back to search opens the default search. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-26 | P01; P04/P07 for additional variations | Return to the actual referring search. | Repeated filters, pagination, mounted-path test, and browser return: passed. | `9b9b739` | Open a profile from a search with filters/page and use Back to search. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-27 | P01; P04/P07 for additional variations | Restore institution-search descriptions. | `test_institution_links_describe_their_searches`: passed. | `9b9b739` | Inspect the education institution link description and destination. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-28 | P01; P04/P07 for additional variations | Restore appointment-search descriptions. | `test_institution_links_describe_their_searches`: passed. | `9b9b739` | Inspect the appointment institution link description and destination. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-29 | P01; P04/P07 for additional variations | Identify the active profile section for assistive tools. | Initial active-state test; browser tabs, bookmark, and View All: passed. | `9b9b739` | Select each section, View All, and a bookmarked section; inspect the active state. Not run. | Await owner deployment, then compare the applicable variation. |
| batch-001-30 | P01; P04/P07 for additional variations | Hide unselected profile sections before scripts run. | Initial template test and desktop/narrow browser checks: passed. | `9b9b739` | Load a profile with scripts delayed, then exercise section controls. Not run. | Await owner deployment, then compare the applicable variation. |

## Local validation

- `uv run ./run_tests.py`: 265 tests passed. The baseline before this batch was 256 passing tests. New regression tests cover all thirty changes, including source variations that may be absent from the selected live profiles.
- Ruff lint and format checks: all seven changed Python files passed.
- Pyright: all seven changed Python files passed with the project interpreter and basic type-checking settings; zero errors or warnings. Pylance was unavailable.
- Browser checks using made-up names and records: seven groups passed at desktop and narrow widths. Checks covered initial visibility without scripts, bookmarks, every section and View All, citation subscript/superscript display, publication filters, actual filtered-search return, direct entry, inactive names, and visible sections below the first screen. No external requests or script errors occurred. These checks do not establish a deployed Rails/Django visual match.
- Saved-source citation comparison against the Rails model: 3,808 distinct citations checked. Visible-text differences fell from 119 to 39; 80 additional citations now match, with no newly differing citations. The remaining 39 differences still need review; this comparison does not check outgoing links or deployed appearance.
- `git diff --check`: passed. Tracked examples use made-up names and records; real data, exact URLs, raw output, and screenshots stay outside Git under private evidence label `batch-001-profile-checks`.

## Handoff and evaluation

After Codex pushes, the owner runs the deploy script and confirms completion. Codex verifies the loaded revision and every planned behavior above, compares selected Rails/Django pages, and updates each result. Keep absent variations, blocked access, and unexplained differences pending in `checklist_todos.md`. Do not move S07 to completed merely because these fixes pass local tests.

Commit and push record: the application changes are committed as `9b9b739` and pushed to `main`. The owner should deploy the latest `main` revision, including these batch records. No deployment confirmation has been received.

Evaluation summary and next-batch candidates: deployed evaluation remains pending. After the owner confirms deployment, compare P01 first and use P04/P07 for missing variations. Prefer remaining differences on the primary profile URL, including any of the 39 saved-citation differences that occur there. Keep unavailable variations pending.
