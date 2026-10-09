# Deployed evaluation: URL batch 007

Evaluated October 5, 2026 on loaded revision `88fb8e4`. Raw observations, exact pairs and screenshots stay outside Git under private comparison record label `url-batch-008-review`. Follow [progress.md](../progress.md) and [the next list](../next_batch.md).

Contents:

- [Recorded changes](#recorded-changes)
- [Whole URL results](#whole-url-results)
- [Check results and limits](#check-results-and-limits)
- [Next implementation](#next-implementation)

## Recorded changes

Both expanded-filter corrections pass after the owner collects the changed static files. Initial requests returned the previous CSS and JavaScript even though the loaded revision and version queries were current. Repeat requests then return bytes matching the local sources. A browser refresh without cached resources is necessary before accepting the rendered result.

| Previous change | Deployed result |
| --- | --- |
| url-batch-007-01: retain alphabetical order among tied counts | Pass. All three More dialogs on SEARCH01 and BROWSE01 retain descending counts and alphabetical ties after A–Z then 9–0, at both widths. Applicable keyboard sorting, narrowing, empty results, paging and reopening pass. Source count differences remain separate. |
| url-batch-007-02: hide cleared loading status | Pass. Each settled target dialog's empty status has zero height; the first row is 15 pixels below the body edge, matching the reference at both widths. Normal loading remains visible; controlled failure and successful retry remain supported by local checks, without deliberately disrupting a deployed service. |

## Whole URL results

TERMS01, HISTORY01 and HELP_VIZ01 each pass four functional and two visual checks. Whole cases advance from nine to twelve. F01 covers full content and applicable controls. F02 covers all internal links/anchors and keyboard navigation, including search submission. F03 covers external/configured destinations. F04 covers required images/assets and relevant browser errors. V01 and V02 cover the full settled desktop and narrow page, from the header through the footer. These definitions are preserved from the preceding list.

External content and email hrefs match the reference. Shared institution links use the configured HTTPS destinations; feedback retains the current page. No email or feedback form is submitted. No content anchor is exposed on these three pages. Required illustrations load; page styles, scripts and fonts have delivery check results, and relevant browser warnings/errors are absent.

P03 completes its six functional and twelve visual checks. All six sections match rendered text, keyboard active states and complete views at both sizes. The three publication-type filters match ordered citations at both sizes. Four distinct internal content destinations preserve their paths and decoded queries; external/email hrefs match and the configured Manager destination is preserved. The linked CV matches every byte and all five rendered pages are inspected. Actual return after selecting two filters and paging retains its originating search. Signed-in PDF HEAD, valid-range and unsatisfied-range responses pass after the owner manually enables Console pasting.

## Check results and limits

Captures record actual bitmap dimensions, scroll position zero at entry, overlapping frames and footer coverage. Incorrect earlier captures and observations made during dialog animations are excluded. Final named-dialog records are authoritative; generic dialog records can retain an earlier dialog during its closing animation and are not proof for another filter. Raw image and pointer differences remain private; no tolerance is widened.

Supporting HTTP requests remain sequential with a pause after each response. Unused CSS image references can fail independently of the current pages; protected portrait requests redirect without browser authentication while the signed-in browser images load. These observations do not certify every asset variation or the homepage's pending backgrounds.

Search count/order, organization membership and homepage book order remain unresolved, with source alignment unconfirmed. Supporting long-title JSON passes on keyword and browse search through permitted read-only Console checks. Other profile URLs retain their earlier partial check results and explicit remaining work. Endpoint families and owner acceptance remain pending. The before-script/source restriction remains in force; no source HTML fetch or authentication extraction is used.

## Next implementation

[URL batch 008](../current_batch.md) adds a deployment-only check for missing or stale collected CSS/JavaScript and documents static collection after every update. Its initial list keeps seventeen unfinished cases and adds Roadmap, Publications Help and the existing additional public page. Roadmap and Publications Help subsequently complete all four functional and two visual checks each, including every Publications anchor. With the completed P03, six whole cases finish during this review and the total reaches fifteen. The refilled next list has sixteen carried cases and four added cases; three newly selected replacements remain unreviewed. The institution-page correction awaits deployment. Partial checks do not increase whole-case totals.
