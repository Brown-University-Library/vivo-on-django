# Goal: Researchers@Brown Rails-to-Django conversion

Replace the Rails front end for Researchers@Brown (R@B) with a Django application that reproduces the existing public site's URLs, actually used functionality, and look and feel as exactly as reasonably possible. Visitors should be able to follow existing links and use the site in the same way after the replacement.

This document defines the intended outcome and boundaries. The [workplan](workplan.md) describes the current sequence of work, batch workflow, and implementation choices.

## Scope

Reproduce the functionality currently used by the public Rails application, including its pages, search and browsing behavior, record displays, downloads, visualizations, and supporting assets or responses wherever these are confirmed to be part of the active site. Preserve relevant query parameters, redirects, navigation, and links to separate services.

The running Rails site is the reference for both behavior and appearance. The saved [public-path list](../../rab_primary_url_paths.md) and [log-analysis summary](../../apache_log_analysis.md) provide evidence for establishing the required URLs; they are historical findings, not a verified or complete set of current requirements. The Rails route definitions and earlier Django prototype also do not, by themselves, determine scope.

## Exclusions

- The unfinished Manager functionality embedded in the Rails source, and other unused routes or features.
- Rebuilding the separate Manager application, the VIVO back end, or related data-management systems. The replacement should continue using the existing services it needs.
- Redesigning the public site or adding new features as part of this conversion.

These boundaries supersede earlier plans to give every Rails route a Django equivalent. Preserving a public link to the separate Manager remains in scope where that link is part of the existing site.

## Success criteria

- The required public URLs and their behavior are confirmed and documented, and the Django application supports that agreed scope.
- Existing public links, user interactions, and connections to supporting services work as expected in the replacement.
- Functional and visual comparisons, including Playwright checks against the running Rails site, demonstrate that the Django site reproduces its behavior and appearance. Comparisons account for changing data and random homepage imagery; any remaining differences are documented for review.

Background: [PROMPTS.md](../../PROMPTS.md), [REPORT__consolidation.md](../../REPORT__consolidation.md), and [REPORT__previous_work.md](../../REPORT__previous_work.md).
