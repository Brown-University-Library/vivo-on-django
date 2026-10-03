# Current batch and URLs being evaluated

Archived when batch-002 starts; see the [current batch](../current_batch.md) for the active handoff. Follow [workplan.md](../workplan.md). Exact Rails and Django URLs are in `../../../current_urls.local.md`, outside the repository. Detailed evidence uses private label `batch-001-profile-checks`.

Contents:

- [Batch status](#batch-status)
- [Current URL cases](#current-url-cases)
- [Changes in this batch](#changes-in-this-batch)
- [Local validation](#local-validation)
- [Handoff and evaluation](#handoff-and-evaluation)

## Batch status

- Batch ID: batch-001.
- State: deployed evaluation recorded; remaining checks and differences need review.
- Started / last updated: October 3, 2026.
- Goal: correct person-profile citations and complete related profile navigation and section display.
- Branch / starting revision: `main` / `4a50060`.
- Implemented and locally checked changes: 30.
- Verified after deployment: 15. No qualifying live variation: 14. Before-JavaScript check blocked: 1.
- Application commit: `9b9b739` (`Improves profile citations and navigation`). Batch-record commit: `e0cec5a`. Both pushed to `main`.
- Owner deployment confirmation: received October 3, 2026.
- Loaded deployed revision: `e0cec5a7e67ddbb51eb5c40b67244eb5251e7be2`, confirmed and rechecked October 3, 2026.
- Next responsible person and action: Codex finishes the primary profile's remaining supporting-link and visual comparisons before selecting another implementation batch. Preserve unverified variations and demonstrated differences in the pending checklist.

The [evaluation report](batch_001_evaluation.md) records all thirty outcomes. No whole URL case is certified complete. Evaluation records are local and uncommitted; the application was not changed during this review.

## Current URL cases

| Pending ID / case IDs | Safe URL pattern and variation | Deployed result / next action |
| --- | --- | --- |
| S07 / P01 | `/display/{person_id}`, full section navigation, no publications | All six section states match Rails rendered text. Matched desktop and narrow Overview views, including content below the first screen, pass. Finish supporting-link and other section appearance checks before whole URL completion. |
| S07 / P04, P07 | `/display/{person_id}`, sparse section content, no publications | Initial controls match. Fresh bookmarked empty sections and View All differ because Django omits headings that Rails displays. Retain as next-batch candidates. |
| S07 / P08–P12 | `/display/{person_id}`, publication and institution variations | Compared 278 citations; 273 match and five chapter-collection spacing differences remain. Applicable citation, outbound-link, institution-search, filter, and section checks pass. Whole URL comparisons remain pending. |
| S07 / P13–P15 | `/display/{person_id}`, editor punctuation, quoted book title, and padded website variation | Improvements 05, 11, and 20 pass on qualifying current source records. The website link reaches its intended article. These targeted results do not certify the whole URLs. |

P01/P04/P07 have no publications, so they cannot demonstrate the citation changes. Exact bindings for the added publication cases are in the private outer URL file. Never edit live records to create test variations. Every required URL-pattern endpoint must eventually have a recorded visual confirmation against Rails before completion; individual fixes and whole endpoint outcomes remain separate.

## Changes in this batch

| Change ID | Case IDs | Observed difference and intended result | Local check and result | Commit | Deployed check and result | Remaining difference / next action |
| --- | --- | --- | --- | --- | --- | --- |
| batch-001-01 | P10 | Avoid repeated periods after article page numbers. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Verified after deployment: Article page punctuation matches Rails on a period-terminated source value. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-02 | Selected variation cases | Avoid repeated periods after chapter page numbers. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Checked locally only: No chapter pages already ending in a period. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-03 | Selected variation cases | Avoid repeated volume separators. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Checked locally only: No volume already ending in a comma. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-04 | Selected variation cases | Avoid repeated issue separators. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Checked locally only: No issue already ending in a comma. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-05 | P13 | Avoid repeated editor separators. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Verified after deployment: Editor text already ending in a comma has one separator and matches Rails. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-06 | Selected variation cases | Avoid repeated publisher separators. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Checked locally only: No publisher already ending in a comma. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-07 | Selected variation cases | Avoid repeated location separators. | `test_citation_separators_match_public_source_rules`: passed. | `9b9b739` | Checked locally only: No location already ending in a comma. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-08 | Selected variation cases | Preserve nested quotation marks in chapter titles. | `test_source_title_and_author_punctuation_is_preserved`: passed. | `9b9b739` | Checked locally only: No qualifying nested chapter quotation marks. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-09 | Selected variation cases | Preserve author ellipses. | `test_source_title_and_author_punctuation_is_preserved`: passed. | `9b9b739` | Checked locally only: No author text ending in multiple periods. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-10 | Selected variation cases | Preserve title ending punctuation. | `test_source_title_and_author_punctuation_is_preserved`: passed. | `9b9b739` | Checked locally only: No quoted title ending in multiple periods. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-11 | P14 | Preserve quotation marks in italic book titles. | `test_source_title_and_author_punctuation_is_preserved`: passed. | `9b9b739` | Verified after deployment: Quoted book title retains quotation marks inside italic text and matches Rails. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-12 | P08, P11 | Render italic text in publication titles. | `test_scientific_title_formatting_and_entities_render_as_text`: passed. | `9b9b739` | Verified after deployment: Italic title elements and text match Rails. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-13 | P08 | Render subscripts in publication titles. | `test_scientific_title_formatting_and_entities_render_as_text`: passed. | `9b9b739` | Verified after deployment: Subscript elements and text match Rails, including narrow display. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-14 | P08, P09 | Render superscripts in publication titles. | `test_scientific_title_formatting_and_entities_render_as_text`: passed. | `9b9b739` | Verified after deployment: Superscript elements and text match Rails. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-15 | Selected variation cases | Display numeric publication volumes. | `test_numeric_metadata_and_blank_journal_fallback`: passed. | `9b9b739` | Checked locally only: No numeric-type volume source value. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-16 | Selected variation cases | Display numeric publication issues. | `test_numeric_metadata_and_blank_journal_fallback`: passed. | `9b9b739` | Checked locally only: No numeric-type issue source value. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-17 | Selected variation cases | Display numeric publication pages. | `test_numeric_metadata_and_blank_journal_fallback`: passed. | `9b9b739` | Checked locally only: No numeric-type pages source value. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-18 | P09, P10 | Trim surrounding spaces from DOI links. | `test_padded_citation_links_reach_the_intended_destination`: passed. | `9b9b739` | Verified after deployment: Padded DOI values produce the expected link; an opened link reaches the intended article. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-19 | P12 | Trim surrounding spaces from PubMed identifiers. | `test_padded_citation_links_reach_the_intended_destination`: passed. | `9b9b739` | Verified after deployment: Padded PubMed ID produces the expected link and reaches the intended article. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-20 | P15 | Trim surrounding spaces from citation website links. | `test_padded_citation_links_reach_the_intended_destination`: passed. | `9b9b739` | Verified after deployment: Padded website value is actually used as More Info, is trimmed, and reaches the intended article. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-21 | Selected variation cases | Use the venue when the journal field is blank. | `test_numeric_metadata_and_blank_journal_fallback`: passed. | `9b9b739` | Checked locally only: No whitespace-only journal paired with a venue. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-22 | P11 | Display encoded ampersands as citation text. | `test_scientific_title_formatting_and_entities_render_as_text`: passed. | `9b9b739` | Verified after deployment: Encoded ampersand displays as normal text and matches Rails. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-23 | Selected variation cases | Display encoded apostrophes as citation text. | `test_scientific_title_formatting_and_entities_render_as_text`: passed. | `9b9b739` | Checked locally only: No encoded apostrophe title value. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-24 | Selected variation cases | Show inactive profile status on narrow screens. | Initial template test and desktop/narrow browser checks: passed. | `9b9b739` | Checked locally only: No inactive profile available in the selected or saved source records. | Keep the deployed demonstration pending until a qualifying source variation is available. |
| batch-001-25 | P01 | Reset stale search-return links on direct visits. | Direct-entry regression, prepared-page test, and browser check: passed. | `9b9b739` | Verified after deployment: Direct entry after a filtered search resets Back to search to default search. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-26 | P01, P08 | Return to the actual referring search. | Repeated filters, pagination, mounted-path test, and browser return: passed. | `9b9b739` | Verified after deployment: Actual Back to search preserves both repeated filters and page 1/page 2. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-27 | P08–P12 | Restore institution-search descriptions. | `test_institution_links_describe_their_searches`: passed. | `9b9b739` | Verified after deployment: Education descriptions and search queries match Rails; an institution search loads and browser Back restores the section. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-28 | P08, P11 | Restore appointment-search descriptions. | `test_institution_links_describe_their_searches`: passed. | `9b9b739` | Verified after deployment: Appointment descriptions and search queries match Rails; an institution search loads and browser Back restores the section. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-29 | P01, P08 | Identify the active profile section for assistive tools. | Initial active-state test; browser tabs, bookmark, and View All: passed. | `9b9b739` | Verified after deployment: All section controls, View All, bookmarks, and keyboard selection set the expected active state. | Individual improvement verified; whole URL checks remain pending. |
| batch-001-30 | P01, P08 | Hide unselected profile sections before scripts run. | Initial template test and desktop/narrow browser checks: passed. | `9b9b739` | Blocked for the before-JavaScript condition. Ordinary initial visibility and controls pass. | Browser approval review blocked page-source viewing. Preserve the local before-script evidence and this limitation. |

## Local validation

- `uv run ./run_tests.py`: 265 tests passed. The baseline before this batch was 256 passing tests. New regression tests cover all thirty changes, including source variations that may be absent from the selected live profiles.
- Ruff lint and format checks: all seven changed Python files passed.
- Pyright: all seven changed Python files passed with the project interpreter and basic type-checking settings; zero errors or warnings. Pylance was unavailable.
- Browser checks using made-up names and records: seven groups passed at desktop and narrow widths. Checks covered initial visibility without scripts, bookmarks, every section and View All, citation subscript/superscript display, publication filters, actual filtered-search return, direct entry, inactive names, and visible sections below the first screen. No external requests or script errors occurred. These checks do not establish a deployed Rails/Django visual match.
- Saved-source citation comparison against the Rails model: 3,808 distinct citations checked. Visible-text differences fell from 119 to 39; 80 additional citations now match, with no newly differing citations. The remaining 39 differences still need review; this comparison does not check outgoing links or deployed appearance.
- `git diff --check`: passed. Tracked examples use made-up names and records; real data, exact URLs, raw output, and screenshots stay outside Git under private evidence label `batch-001-profile-checks`.

## Handoff and evaluation

The owner confirmed deployment. Codex evaluated the loaded revision and recorded fifteen direct deployed passes, fourteen absent variations, and one blocked before-script check. All thirty have passing local regression evidence. The focused regression rerun passed nine test methods. Application code and its pushed commits remain unchanged during evaluation.

See the [evaluation report](batch_001_evaluation.md) and [pending checklist](../checklist_todos.md). Next-batch candidates are the demonstrated chapter-collection spacing differences and sparse-profile empty-section/bookmark differences. First finish the primary profile's remaining supporting-link and visual checks. Do not certify S07, accept unexplained differences, or replace this batch merely because the available improvements passed.
