# Goal: Researchers@Brown Rails-to-Django conversion

Historical record from revision `8c5c8ce`, preserved during the October 9, 2026 cleanup. The owner considers the conversion review complete. Any pending labels, acceptance instructions, or workflow directions below describe the earlier conversion; they are not current tasks.

Replace the Rails front end for Researchers@Brown (R@B) with a Django application that reproduces the existing public site's URLs, actually used functionality, and look and feel as exactly as reasonably possible. Visitors should be able to follow existing links and use the site in the same way after the replacement.

This document defines the intended outcome and boundaries. The workplan describes the current sequence of work, batch workflow, and implementation choices.

When Rails behavior appears wrong, Codex first applies the owner's recorded conditional guidance under the owner-decision procedure. Queue a nonurgent owner question under optional comparison reviews when that guidance does not resolve the case or its expected outcome. Record each applicable choice in [accepted_differences.md](../decisions/accepted_differences.md). An owner-approved correction is a narrow exception to exact matching and the exclusion of new behavior; it does not authorize a broader redesign. Approval of this procedure alone accepts no individual difference.

Verification of equivalent repeated data and controls follows [RC01](../methods/completion_checks.md#approved-procedure-for-repeated-checks). Codex compares complete data and destination addresses, then checks selected normal and edge examples at both widths. Every required endpoint and distinct state retains its visual and behavior requirements. Record affected check revisions before applying this procedure; it accepts no individual difference and changes no completion state by itself.

## Scope

Reproduce the functionality currently used by the public Rails application, including its pages, search and browsing behavior, record displays, downloads, visualizations, and supporting assets or responses wherever these are confirmed to be part of the active site. Preserve relevant query parameters, redirects, navigation, and links to separate services.

The running Rails site is the reference for both behavior and appearance. The saved public-path list and log-analysis summary help establish the required URLs; they are historical findings, not a verified or complete set of current requirements. The Rails route definitions and earlier Django prototype also do not, by themselves, determine scope.

## Exclusions

- The unfinished Manager functionality embedded in the Rails source, and other unused routes or features.
- Rebuilding the separate Manager application, the VIVO back end, or related data-management systems. The replacement should continue using the existing services it needs.
- Redesigning the public site or adding new features as part of this conversion.
- The nine local account routes and seven editing routes the owner commented out in `config/urls.py` on October 6, 2026. Their exact patterns are in the endpoint exclusions. Do not implement or require comparison results for these routes.

These boundaries supersede earlier plans to give every Rails route a Django equivalent. Preserving a public link to the separate Manager remains in scope where that link is part of the existing site.

## Success criteria

- The required public URLs and their behavior are confirmed and documented, and the Django application supports that agreed scope.
- Existing public links, user interactions, and connections to supporting services work as expected in the replacement.
- Functional and visual comparisons, including Playwright checks against the running Rails site, demonstrate that the Django site reproduces its behavior and appearance. Comparisons account for changing data and random homepage imagery; any remaining differences are documented for review.
- Every required URL-pattern endpoint must eventually be confirmed visually against Rails before it is marked complete. Record the compared state and check results for each endpoint and its required variations. For redirects, data responses, downloads, and assets, record what was visually inspected, such as the destination page, displayed response, downloaded document, or consuming page; also retain the applicable response and behavior checks.

Background: PROMPTS.md, REPORT__consolidation.md, and REPORT__previous_work.md.
