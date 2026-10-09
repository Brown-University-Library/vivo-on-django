# Application server operation

These procedures apply to the current application. Keep actual configuration, addresses, credentials, and logs outside Git. The installation's Shibboleth restriction is managed separately from Django's allowed-host setting.

## Contents

- [Prepare the installation](#prepare-the-installation)
- [Check code and static files](#check-code-and-static-files)
- [Source checks](#source-checks)
- [Restart and verify](#restart-and-verify)

## Prepare the installation

1. Keep the private environment file outside the checkout. Configure live sources using [source configuration](source_journey.md), or supply compatible external inputs for a retained offline mode.
2. Create the writable directories required by database, cache, logs, and STATIC_ROOT settings.
3. Install locked packages with the appropriate group: `uv sync --locked --group staging` or `uv sync --locked --group prod`. The groups supply PyMySQL for homepage books. Use the existing process manager and WSGI configuration.
4. Keep the existing access restriction. ALLOWED_HOSTS_JSON checks the requested hostname; it does not authenticate visitors.

For configured teams/custom organizations, copy the private membership file outside the checkout and set TEAM_SOURCE_MANIFEST. A valid workstation file does not establish that the server process can read it.

## Check code and static files

Run from the checkout:

```console
uv run ./manage.py check
uv run ./manage.py migrate --plan
uv run ./manage.py migrate
uv run ./manage.py collectstatic --noinput
uv run ./manage.py check --deploy --tag staticfiles
```

Check reads configuration. Migrate --plan shows pending table changes; migrate applies them. Collectstatic copies application assets to STATIC_ROOT. Run it after code updates that change assets.

The staticfiles-tagged check compares current CSS/JavaScript files with collected copies without making service requests or writing files. After missing or stale copies, run collectstatic and repeat it. It does not verify web-server mapping, browser caches, fonts, or images; inspect actual delivered assets too.

A general `uv run ./manage.py check --deploy` also reports settings that depend on HTTPS handling. Coordinate those settings with the system administrator and the existing server configuration.

## Source checks

Without --source, this checks the selected mode and validates prepared inputs if selected; it makes no source-service requests:

```console
uv run ./manage.py check_dev_sources
```

With --source, the command checks only named live services, independently of PAGE_DATA_MODE. These commands send read-only requests or read active book rows. They change no source data or environment values:

```console
uv run ./manage.py check_dev_sources --source solr
uv run ./manage.py check_dev_sources --source search --search-query "$QUERY"
uv run ./manage.py check_dev_sources --source search-facets --search-query "$QUERY"
uv run ./manage.py check_dev_sources --source profile --vivo-id "$PERSON_ID"
uv run ./manage.py check_dev_sources --source viz
uv run ./manage.py check_dev_sources --source vivo --vivo-id "$PERSON_ID"
uv run ./manage.py check_dev_sources --source books
```

Solr reads a count. Search/facets exercise their processors. Profile checks the requested person's collaborator data. Viz reads an availability list. VIVO reports status and a digest of the selected JSON-LD response. Books reads active rows and checks the image prefix. Failures return a nonzero exit status. Printed results omit actual addresses and returned record content.

## Restart and verify

After environment changes, restart through the existing process manager. Check /version/: loaded_version identifies the revision loaded by the process, while version can reflect a newer checkout before restart.

Load affected pages through the existing access restriction. Check returned content and delivered assets, including a search, profile, organization, and homepage when their sources change. Workstation access and a successful version response do not establish server-source connectivity.

Retained prepared mode also needs a compatible external bundle. `uv run ./manage.py validate_prepared_data` checks it without service requests. Fix the configured path or supply the required files, then restart to load a new bundle. See [the retained-code review](code_retirement_review.md).
