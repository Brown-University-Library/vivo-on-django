# Historical browser comparison method

This is a summary of the conversion method, not an active batch workflow. [Current browser instructions](../../docs/browser_comparison.md) describe the retained tool.

The conversion captured selected reference pages and compared current Django pages at matching browser versions, viewport sizes, loading states, and scroll positions. Reports kept text/status observations alongside screenshots and amplified pixel differences.

Complete-page inspection included lower content and the footer. Controls, keyboard actions, Back/Forward history, linked documents, literal destinations, response metadata, and actual delivered assets were checked separately where relevant.

Saved comparisons could be reused when current source content, code, styles, images/fonts, geometry, and control state still matched their reviewed conditions. Changed or incomplete regions needed new inspection. Repeated equivalent content did not remove the need to inspect a unique endpoint's complete layout and behavior.

Raw browser output and exact record bindings stayed outside Git. The earlier workplan's batch selection, daily cutoffs, and progress accounting are retired.
