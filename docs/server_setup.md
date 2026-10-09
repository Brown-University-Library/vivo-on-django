# First development-server installation

This first installation runs Django with the saved prepared-data bundle. It checks the Python environment, Django settings, static files, database migrations, and access to the saved bundle. It does not contact Solr, VIVO, the visualization service, or the Rails database.

## Prepare the installation

1. Copy `example.env` to the private `.env` beside the Git checkout and fill the active values. Use `PAGE_DATA_MODE=prepared`. Copy the prepared-data directory separately and set `PREPARED_FIXTURE_DIR` to its location.
2. Create the writable directories named by `STATIC_ROOT` and by the current database, cache, and log settings in `config/settings.py`.
3. Install the locked application dependencies with `uv sync --locked`.
4. Restrict access to the site through the server or proxy configuration while this work is in progress. Django's `ALLOWED_HOSTS_JSON` checks the requested hostname; it is not an access restriction.

The first installation needs no Solr, VIVO, visualization-service, or Rails database values. Prepared mode does not request those services. When the installation moves to live visualization data, configure `VIZ_SERVICE_URL` in its private `.env` and check that the application server can read the chosen service directly. Exact data comparisons require corresponding source data. When the owner keeps separate staging sources, verify independent behavior and retain data differences for the later production comparison; do not change source services without authorization.

## Check and start Django

Run these commands from the Django checkout, with the private `.env` in the outer directory:

```console
uv run ./manage.py check
uv run ./manage.py validate_prepared_data
uv run ./manage.py migrate --plan
uv run ./manage.py migrate
uv run ./manage.py collectstatic --noinput
uv run ./manage.py check --deploy
```

`check` should report prepared-data mode and the selected bundle version. `validate_prepared_data` checks the bundle manifest, saved page data, and saved assets without contacting another server. `migrate --plan` shows pending database changes; `migrate` applies them to Django's database. `collectstatic` copies Django's CSS, JavaScript, fonts, and images to `STATIC_ROOT`.

`check --deploy` also reports settings that depend on how HTTPS is handled. Decide with the system administrator whether Django or the front-end server redirects HTTP to HTTPS and sets secure cookies. Enable HSTS only after HTTPS works for the entire hostname; a mistaken HSTS setting affects later browser visits and is hard to reverse quickly.

Start the application with the server's normal process manager and WSGI command. Then request the homepage, one search, one profile, and one organization page through the restricted development address. Check that the browser loads `/static/` files and `/__prepared_assets/` files successfully.

## What to record for the next work

Record the Django version, prepared bundle version, browser-comparison report location, and any failed command or request. Keep server paths, hostnames, addresses, credentials, and raw logs outside Git.

The first server comparison should use the browser command's `compare-target` mode. It visits the configured restricted Django address and compares selected pages with a saved public-site baseline. This verifies the deployed Django output while still using saved prepared data. Source integration remains a later step.

### Repeatable checks after a deployment

Run these commands from the Django checkout on the development server. The command reads the private `.env` loaded by Django and prints status without printing source addresses or returned records. With no `--source` option, it checks the selected page-data mode and makes no service requests.

```console
uv run ./manage.py check_dev_sources
uv run ./manage.py check
uv run ./manage.py collectstatic --noinput
uv run ./manage.py check --deploy --tag staticfiles
```

Run `collectstatic` after every code update, before calling deployment complete. It copies changed static files into `STATIC_ROOT`; new asset version queries alone do not update those copies. The scheduled update caller performs collection as part of automatic deployment. Confirm that its static-collection option is enabled. Codex follows [the workplan's automatic checks](../WORKPLAN_STUFF/workplan.md#automatic-deployment-and-verification) without waiting for an owner message. When authorized server access exists, run the command checks below; otherwise record them as not run and retain separate browser delivery checks.

`check --deploy --tag staticfiles` reads the application's CSS and JavaScript source files and compares their contents with the collected copies. It reports an error when a copy is missing, unreadable, or stale. It contacts no server and changes no files or application data. Ordinary startup checks skip this comparison. After an error, run `collectstatic` and repeat the check.

This check expects the ordinary copied files used by this application. It does not verify the web server's static directory mapping, cache contents, fonts, or images. Codex separately checks the actual served asset bytes and rendered behavior. A current `/version/` response and current asset query values do not prove that the browser received current CSS or JavaScript. If the served bytes match but the browser still uses older files, refresh that page without its cached resources and repeat the comparison.

If the root page reports a missing prepared manifest, set `PREPARED_FIXTURE_DIR` in the server's private `.env` to the separately copied bundle directory. The directory must contain `manifest.json` and its referenced files, remain readable by the Django process, and be outside the Git checkout. Relative values resolve against the Django checkout. Then run `uv run ./manage.py validate_prepared_data` and restart the application; prepared bundles are cached per process. A valid local bundle or a successful `/version/` response does not establish that the server has this bundle.

Scoped active teams and custom organizations also require `TEAM_SOURCE_MANIFEST`. Copy the privately prepared JSON membership file outside the Git checkout and set this variable to its location; relative paths resolve against the Django checkout. The file supplies names and fixed member lists defined by the Rails code. It does not replace the configured Solr or visualization service, and ordinary organizations do not require it. Keep real membership files out of Git. If a page reports that the member source manifest is not configured, the running setting is empty. Configure the file, restart the application through its existing process manager, then reload the affected page and check its members and navigation. A valid workstation file alone does not prove that the application server has loaded it.

When moving to live data, set `PAGE_DATA_MODE=live` and configure each needed source in the private `.env`. Check one source at a time from the development server:

```console
uv run ./manage.py check_dev_sources --source solr
uv run ./manage.py check_dev_sources --source viz
uv run ./manage.py check_dev_sources --source vivo --vivo-id EXISTING_RECORD_ID
uv run ./manage.py check_dev_sources --source books
```

When `--source` is supplied, the command checks only the named live services. It does not validate `PAGE_DATA_MODE` or look for prepared data, so a missing prepared manifest cannot cause a source check to fail. The Solr check sends one count query. The visualization check reads one graph-availability list. The VIVO check reads one existing record's JSON-LD export and prints its HTTP status and a SHA-256 digest, so the same record can be checked against another configured backend without printing its content. A 404 means that record was not found at the configured backend. The books check reads the active homepage rows and checks the image prefix; it needs the `staging` dependency group for the database driver. Each selected source check exits nonzero on failure. These checks use Django's source client and make read-only requests; they do not switch `PAGE_DATA_MODE` or change `.env`.

After changing `.env`, restart Django and repeat the relevant command. Request `/version/` and compare `response.loaded_version` with the expected revision; `response.version` can show an updated checkout before restart. Then load the root page and a selected search and profile through the existing access restriction. Compare source-backed results with the public site only after confirming which Solr index, VIVO backend, and visualization service the development process actually uses. The nightly Solr copy may have a different refresh time, and the development VIVO backend may contain different records.
