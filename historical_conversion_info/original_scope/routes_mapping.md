# Rails → Django Routes Mapping

Historical record from revision `8c5c8ce`, preserved during the October 9, 2026 cleanup. The owner considers the conversion review complete. Any pending labels, acceptance instructions, or workflow directions below describe the earlier conversion; they are not current tasks.

Contents:

- [Home and Static](#home-and-static)
- [Display](#display)
- [Visualizations](#visualizations)
- [Reports](#reports)
- [Search](#search)
- [Legacy VIVO and Files](#legacy-vivo-and-files)
- [Individual (legacy VIVO)](#individual-legacy-vivo)
- [Editor (current endpoints present in code; de-prioritized)](#editor-current-endpoints-present-in-code-de-prioritized)
- [Editor (additional Rails endpoints not yet mapped; de-prioritized)](#editor-additional-rails-endpoints-not-yet-mapped-de-prioritized)

Notes:
- Trailing slashes follow Django’s default; we’re not overriding APPEND_SLASH.
- All views honor `?format=json` and return JSON stubs via `render_or_stub()`.
- Legacy `individual` export also supports dotted extensions like `.json`.

## Home and Static
- Rails: `root 'home#index'` → Django: `/` → View: `home_index`
- Rails: `get 'about' => 'home#about'` → Django: `/about/` → `home_about`
- Rails: `get 'faq' => 'home#faq'` → Django: `/faq/` → `home_faq`
- Rails: `get 'help' => 'home#help'` → Django: `/help/` → `home_help`
- Rails: `get 'help/viz' => 'home#help_viz'` → Django: `/help/viz/` → `home_help_viz`
- Rails: `get 'history' => 'home#history'` → Django: `/history/` → `home_history`
- Rails: `get 'publications' => 'home#publications'` → Django: `/publications/` → `home_publications`
- Rails: `get 'roadmap' => 'home#roadmap'` → Django: `/roadmap/` → `home_roadmap`
- Rails: `get 'termsOfUse' => 'home#termsofuse'` → Django: `/termsOfUse/` → `home_terms`
- Rails: `get 'status' => 'home#status'` → Django: `/status/` → `home_status`
- Rails: `get 'brown' => 'home#brown'` → Django: `/brown/` → `home_brown`
- Rails: `get 'side_stuff/brown_classic/:name'` and `get 'side_stuff/brown_classic/'` →
  Django: `/side_stuff/brown_classic/<name>/` and `/side_stuff/brown_classic/` → `home_brown_classic`

## Display
- Rails: `get 'display/' => 'display#index'` → Django: `/display/` → `display_index`
- Rails: `get 'display/:id' => 'display#show'` → Django: `/display/<id>/` → `display_show`
- Rails: `get 'display/:id/publications' => 'display#show_publications'` →
  Django: `/display/<id>/publications/` → `display_publications`

## Visualizations
- Rails: `get 'display/:id/viz' => 'visualization#home'` → Django: `/display/<id>/viz/` → `visualization_home`
- Rails: `get 'display/:id/viz/coauthor'` → Django: `/display/<id>/viz/coauthor/` → `visualization_coauthor`
- Rails: `get 'display/:id/viz/coauthor_treemap'` → Django: `/display/<id>/viz/coauthor_treemap/` → `visualization_coauthor_treemap`
- Rails: `get 'display/:id/viz/collab'` → Django: `/display/<id>/viz/collab/` → `visualization_collab`
- Rails: `get 'display/:id/viz/publications'` → Django: `/display/<id>/viz/publications/` → `visualization_publications`
- Rails: `get 'display/:id/viz/research'` → Django: `/display/<id>/viz/research/` → `visualization_research`

## Reports
- Rails: `get 'reports/subject-lib'` → Django: `/reports/subject-lib/` → `subject_lib_list`
- Rails: `get 'reports/subject-lib/:list_id'` → Django: `/reports/subject-lib/<list_id>/` → `subject_lib`

## Search
- Rails: `get 'search' => 'search#index'` → Django: `/search/` → `search`
- Rails: `get 'search/advanced'` → Django: `/search/advanced/` → `advanced_search`
- Rails: `get 'search_facets' => 'search#facets'` → Django: `/search_facets/` → `search_facets`

## Legacy VIVO and Files
- Rails: `get 'people' => 'home#people'` → Django: `/people/` → `people`
- Rails: `get 'ous' => 'home#organizations'` → Django: `/ous/` → `organizations`
- Rails: `get 'file/:id/:file_name' => 'display#old_image'` →
  Django: `/file/<id>/<file_name>/` → `old_image` (returns 404 stub until implemented)

## Individual (legacy VIVO)
- Rails: `get 'individual/:id' => 'individual#redirect'` → Django: `/individual/<id>/` → `individual_redirect`
- Rails: `get 'individual/:id/:id.:format' => 'individual#export'` and `get 'individual/:id.:format'` →
  Django: `/individual/<id>/<id2>.<fmt>/` and `/individual/<id>.<fmt>/` (regex) → `individual_export`
  - JSON supported via extension or `?format=json`

## Editor (current endpoints present in code; de-prioritized)
- Rails: `get 'edit/fast/search'` → Django: `/edit/fast/search/` → `edit_fast_search`
- Rails: `post 'edit/overview/:faculty_id/update'` → Django: `/edit/overview/<faculty_id>/update` → `overview_update`
- Rails: `post 'edit/research_area/:faculty_id/add'` → Django: `/edit/research_area/<faculty_id>/add` → `research_area_add`
- Rails: `post 'edit/research_area/:faculty_id/delete'` → Django: `/edit/research_area/<faculty_id>/delete` → `research_area_delete`
- Rails: `post 'edit/web_link/:faculty_id/save'` → Django: `/edit/web_link/<faculty_id>/save` → `web_link_save`
- Rails: `post 'edit/web_link/:faculty_id/delete'` → Django: `/edit/web_link/<faculty_id>/delete` → `web_link_delete`

## Editor (additional Rails endpoints not yet mapped; de-prioritized)
- `edit/research/overview/:faculty_id/update`
- `edit/research/statement/:faculty_id/update`
- `edit/research/funded/:faculty_id/update`
- `edit/research/scholarly/:faculty_id/update`
- `edit/background/awards/:faculty_id/update`
- `edit/affiliations/text/:faculty_id/update`
- `edit/teaching/overview/:faculty_id/update`
