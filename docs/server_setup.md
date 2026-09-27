# First development-server installation

This first installation runs Django with the saved prepared-data bundle. It checks the Python environment, Django settings, static files, database migrations, and access to the saved bundle. It does not contact Solr, VIVO, the visualization service, or the Rails database.

## Prepare the installation

1. Copy `example.env` to the private `.env` beside the Git checkout and fill the active values. Use `PAGE_DATA_MODE=prepared`. Copy the prepared-data directory separately and set `PREPARED_FIXTURE_DIR` to its location.
2. Create the writable directories named by `STATIC_ROOT` and by the current database, cache, and log settings in `config/settings.py`.
3. Install the locked application dependencies with `uv sync --locked`.
4. Restrict access to the site through the server or proxy configuration while this work is in progress. Django's `ALLOWED_HOSTS_JSON` checks the requested hostname; it is not an access restriction.

The first installation needs no Solr, VIVO, visualization-service, or Rails database values. The commented source settings in `example.env` record what later work will need, but Django does not read them yet.

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
