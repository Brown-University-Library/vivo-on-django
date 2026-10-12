# Application server operation

These procedures apply to the current application. Keep actual configuration, addresses, credentials, and logs outside Git. The installation's Shibboleth restriction is managed separately from Django's allowed-host setting.

## Contents

- [Prepare the installation](#prepare-the-installation)
- [Check code and static files](#check-code-and-static-files)
- [Source checks](#source-checks)
- [Protected reports](#protected-reports)
- [Restart and verify](#restart-and-verify)

## Prepare the installation

1. Keep the private environment file outside the checkout. Configure sources using [source configuration](source_journey.md).
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

Without --source, this checks required source configuration; it makes no source-service requests:

```console
uv run ./manage.py check_dev_sources
```

With --source, the command checks only named services. These commands send read-only requests or read active book rows. They change no source data or environment values:

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

## Protected reports

1. Place the private report-definition JSON outside the checkout, with read access for Django. Set `REPORT_DEFINITIONS_PATH`; relative paths resolve against the checkout. See [the file format](source_journey.md#subject-librarian-reports). No report migration is needed.
2. Configure Shibboleth on both dev and prod to admit eligible staff to every Django report path, including the two list forms, extensionless downloads, CSV/XML downloads, slash aliases, and the application mount prefix. Configure sign-in to return staff to their requested Django URL.
3. Supply `Shibboleth-isMemberOf` as a trusted WSGI request-environment attribute. Set `REPORTS_SHIB_ATTRIBUTE` if the environment name differs. Use the server's attribute/environment integration rather than ordinary HTTP request headers. Django checks for a nonempty value; staff eligibility remains the web server's responsibility.
4. Leave `REPORTS_ALLOW_LOCAL_DEVELOPMENT=false` on both deployed servers, including dev. The workstation exception is limited to Django's loopback-bound development server.
5. Ensure Django can write its file-based cache and `REPORT_CACHE_LOCK_DIR`, with both shared by workers on that server and outside publicly served directories. Cache entries contain report data. Set `REPORT_CACHE_TIMEOUT_SECONDS` if eight hours is unsuitable, then restart Django after environment changes.
6. Test staff sign-in and return, rejected access, both list paths, every download form, and repeated CSV/XML downloads on dev. Compare fresh output with Rails using a zero timeout for the comparison, then restore the chosen timeout and verify reuse. Repeat access and download checks on prod when deploying. A local browser comparison cannot verify server access rules.

## Restart and verify

After environment changes, restart through the existing process manager. Check /version/: loaded_version identifies the revision loaded by the process, while version can reflect a newer checkout before restart.

Load affected pages through the existing access restriction. Check returned content and delivered assets, including a search, profile, organization, and homepage when their sources change. Workstation access and a successful version response do not establish server-source connectivity.

Remove obsolete data-selection and saved-bundle entries from the private environment file when updating an older installation. Keep a private copy of the prior configuration if reverting the code may be necessary. Preserve source-service settings and TEAM_SOURCE_MANIFEST.

After stylesheet renames, run collectstatic and verify that the organization page requests css/organization.css successfully. Check browser caches and the actual delivered files. Avoid deleting shared static output blindly.
