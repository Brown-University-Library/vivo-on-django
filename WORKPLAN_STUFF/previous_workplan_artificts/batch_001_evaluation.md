# Batch 001 deployed evaluation

October 3, 2026. Application commit `9b9b739`; deployed revision `e0cec5a`. The owner confirmed deployment and browser sign-in. Private comparison record label: `batch-001-profile-checks`; exact bindings and detailed observations remain outside Git. This report records available check results, not owner acceptance or whole URL completion.

Contents:

- [Results](#results)
- [Per-improvement checks](#per-improvement-checks)
- [Visual comparisons and remaining differences](#visual-comparisons-and-remaining-differences)
- [Next actions](#next-actions)

## Results

Fifteen of thirty improvements have direct deployed check results. Fourteen remain checked locally only because no qualifying current variation was available in the selected cases or saved sources. One before-JavaScript check remains blocked. No planned improvement was demonstrated to fail; absence of an example is not a deployed pass.

The original three profiles contain no publications. Added eight publication cases for specific source variations. Compared 278 citations across P08–P12: 273 match Rails and five chapter-collection spacing differences remain. P13–P15 provide targeted checks for editor punctuation, book quotation marks, and a displayed padded website link. Do not add their unreviewed citations to the 278 comparison count.

All thirty improvements passed local regression checks. The focused rerun passed nine test methods covering the batch through subtests. No application code changed during evaluation. The safe evaluation and workplan records are retained with the subsequent implementation batch.

## Per-improvement checks

| Improvement | Cases | Deployed outcome and check results | Next action |
| --- | --- | --- | --- |
| batch-001-01 | P10 | Verified after deployment. Article page punctuation matches Rails on a period-terminated source value. | Retain the result; finish whole URL comparisons separately. |
| batch-001-02 | Selected variation cases | Checked locally only. No chapter pages already ending in a period. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-03 | Selected variation cases | Checked locally only. No volume already ending in a comma. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-04 | Selected variation cases | Checked locally only. No issue already ending in a comma. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-05 | P13 | Verified after deployment. Editor text already ending in a comma has one separator and matches Rails. | Retain the result; finish whole URL comparisons separately. |
| batch-001-06 | Selected variation cases | Checked locally only. No publisher already ending in a comma. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-07 | Selected variation cases | Checked locally only. No location already ending in a comma. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-08 | Selected variation cases | Checked locally only. No qualifying nested chapter quotation marks. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-09 | Selected variation cases | Checked locally only. No author text ending in multiple periods. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-10 | Selected variation cases | Checked locally only. No quoted title ending in multiple periods. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-11 | P14 | Verified after deployment. Quoted book title retains quotation marks inside italic text and matches Rails. | Retain the result; finish whole URL comparisons separately. |
| batch-001-12 | P08, P11 | Verified after deployment. Italic title elements and text match Rails. | Retain the result; finish whole URL comparisons separately. |
| batch-001-13 | P08 | Verified after deployment. Subscript elements and text match Rails, including narrow display. | Retain the result; finish whole URL comparisons separately. |
| batch-001-14 | P08, P09 | Verified after deployment. Superscript elements and text match Rails. | Retain the result; finish whole URL comparisons separately. |
| batch-001-15 | Selected variation cases | Checked locally only. No numeric-type volume source value. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-16 | Selected variation cases | Checked locally only. No numeric-type issue source value. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-17 | Selected variation cases | Checked locally only. No numeric-type pages source value. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-18 | P09, P10 | Verified after deployment. Padded DOI values produce the expected link; an opened link reaches the intended article. | Retain the result; finish whole URL comparisons separately. |
| batch-001-19 | P12 | Verified after deployment. Padded PubMed ID produces the expected link and reaches the intended article. | Retain the result; finish whole URL comparisons separately. |
| batch-001-20 | P15 | Verified after deployment. Padded website value is actually used as More Info, is trimmed, and reaches the intended article. | Retain the result; finish whole URL comparisons separately. |
| batch-001-21 | Selected variation cases | Checked locally only. No whitespace-only journal paired with a venue. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-22 | P11 | Verified after deployment. Encoded ampersand displays as normal text and matches Rails. | Retain the result; finish whole URL comparisons separately. |
| batch-001-23 | Selected variation cases | Checked locally only. No encoded apostrophe title value. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-24 | Selected variation cases | Checked locally only. No inactive profile available in the selected or saved source records. | Wait for a qualifying real source variation; do not alter live records. |
| batch-001-25 | P01 | Verified after deployment. Direct entry after a filtered search resets Back to search to default search. | Retain the result; finish whole URL comparisons separately. |
| batch-001-26 | P01, P08 | Verified after deployment. Actual Back to search preserves both repeated filters and page 1/page 2. | Retain the result; finish whole URL comparisons separately. |
| batch-001-27 | P08–P12 | Verified after deployment. Education descriptions and search queries match Rails; an institution search loads and browser Back restores the section. | Retain the result; finish whole URL comparisons separately. |
| batch-001-28 | P08, P11 | Verified after deployment. Appointment descriptions and search queries match Rails; an institution search loads and browser Back restores the section. | Retain the result; finish whole URL comparisons separately. |
| batch-001-29 | P01, P08 | Verified after deployment. All section controls, View All, bookmarks, and keyboard selection set the expected active state. | Retain the result; finish whole URL comparisons separately. |
| batch-001-30 | P01, P08 | Blocked before scripts run. Ordinary initial Overview visibility and controls pass. | Keep the specific before-script condition unverified; retain local check results. |

## Visual comparisons and remaining differences

Every required URL-pattern endpoint must eventually be confirmed visually against Rails before being marked complete. Record its required variations and the actual page or artifact inspected. Successful behavior or response checks alone do not satisfy this requirement.

P01 has matching rendered text and visible panels for Overview, Research, Background, Affiliations, Teaching, and View All. Matched desktop Overview screenshots at 1280×720 and narrow Overview screenshots at 390×844 show matching appearance, including content below the first screen. The Manage your Profile link is present and visible at desktop on both sites; the earlier missing-link suspicion was not confirmed. Other section appearance and supporting-link checks remain pending, so P01 is not complete.

P08–P12 citation comparisons preserve order, inline scientific formatting, and applicable links. DOI, PubMed, and the additional P15 website variation reach their intended articles. Search-return journeys preserve repeated filters and pagination; institution link descriptions and tested searches match; section controls, keyboard selection, bookmarks, and publication filters pass their specific checks. These results do not certify all profile appearance or supporting endpoints.

Remaining demonstrated differences:

- P10 has five chapter-collection titles where Rails retains spaces inside italic text before a comma and Django trims them.
- P04 View All includes an empty Affiliations heading on Rails and omits it on Django. A fresh Affiliations bookmark shows that empty section on Rails and Overview on Django. Background and Teaching bookmarks match.
- P07 fresh Background, Affiliations, and Teaching bookmarks show the corresponding empty heading on Rails and Overview on Django. View All includes those empty headings on Rails and omits them on Django. A matched desktop Teaching screenshot pair confirms the visible difference.

Fresh bookmarked checks reload both pages before comparison. Changing only a fragment on an already loaded Rails page can retain its prior selected state; that observation must not be mistaken for a fresh bookmarked load.

Before-JavaScript visibility remains blocked: automatic browser approval review rejected page-source viewing because the requested protocol is not allowed. No alternate route was used to obtain the blocked source. Ordinary visible-page checks and local initial-template tests do not prove this specific deployed condition.

## Next actions

1. Resume P01 supporting-link and remaining section appearance comparisons when browser automation is available. The later batch record explains the current browser dependency. Prefer completing this individual URL over spreading another feature across profiles.
2. Preserve fourteen absent variation checks and the blocked before-script check as pending; never report all thirty as deployed verified.
3. Prepare focused fixes for the demonstrated collection-title spacing and sparse-profile empty-section behavior when implementation resumes. Recheck applicable publication and full-profile cases after those changes.
4. Keep S07 and all whole profile cases pending until their required functional and visual comparisons pass or the owner explicitly accepts documented differences. Maintain endpoint-by-endpoint saved visual checks across the full scope.
