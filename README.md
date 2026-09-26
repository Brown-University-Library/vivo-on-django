# vivo-on-django

## Brief overview

This project builds a Django replacement for the public Researchers@Brown Rails front end. Its goal is to preserve the site's existing URLs, used functionality, and appearance so visitors can follow the same links and use the site in the same way.

This readme will be updated as the project progresses, until it becomes simply an operational readme for the Django webapp.

## More info

- [Brief overview](#brief-overview)
- [More info](#more-info)
- [Local installation](#local-installation)
- [Usage](#usage)
- [Tests](#tests)
- [Primary dependencies](#primary-dependencies)

[GOAL.md](GOAL.md) defines the scope and success criteria. The running public Rails site is the reference for pages, search and browsing, record displays, downloads, visualizations, query parameters, redirects, and supporting assets. Historical route lists and earlier prototypes help identify what to inspect; only functionality confirmed to be in use belongs in the conversion.

The work preserves links to separate services where the public site uses them. It excludes rebuilding the separate Manager application, unused Manager features in the Rails source, the VIVO back end, and related data-management systems. Redesigns and new features are also outside the conversion's scope.

**Access to Solr is required for the intended application.** Solr supplies the search index used by the existing site. Providing, configuring, populating, and operating that service are currently outside this webapp's scope. The conversion must use the existing Solr service.

The Django implementation is still a prototype. Several pages use sample data, and search, visualization, and other routes include placeholders. The code does not yet provide Solr connection settings or a Solr client. Starting the local app therefore does not establish that real search or the full conversion works. Completion requires functional and visual comparisons against the public Rails site, accounting for changing data and random homepage imagery.

## Local installation

Install Git and uv, and ensure you can access this repository. uv manages the interpreter required by [pyproject.toml](pyproject.toml). The steps below prepare the current prototype with a local SQLite database; work with real research data also requires separately arranged access to Solr. This repository does not set up that service.

1. Start in the parent directory where you want to keep the checkout and its local support files:

   ```bash
   mkdir vivo_on_django_stuff
   cd vivo_on_django_stuff
   git clone https://github.com/birkin/vivo-on-django.git vivo-on-django
   cd vivo-on-django
   ```

2. Install the locked dependencies and create the directories used by the local settings:

   ```bash
   uv sync --locked
   mkdir -p ../DBs ../cache_dir ../logs
   ```

   uv creates the checkout's `.venv` and may download the interpreter and packages. The other directories sit beside the checkout in `vivo_on_django_stuff` and hold the SQLite database, cached responses, and logs.

3. Create `../.env` in your editor, or update it if it already exists. Use the following as the minimum local configuration, choosing your own local development secret:

   ```dotenv
   DJANGO_SECRET_KEY=replace-with-your-local-development-secret
   DJANGO_DEBUG=True
   ALLOWED_HOSTS_JSON=["localhost", "127.0.0.1"]
   STATIC_URL=/static/
   STATIC_ROOT=../staticfiles
   ```

   [config/settings.py](config/settings.py) loads environment values through `python-dotenv`. Keep the file in the outer directory, outside the Git checkout. Preserve any existing settings you need. The checked-in `sample.env` omits required settings and uses some names that the current code does not read; use the names above for this setup. `STATIC_URL` is a browser URL prefix, while `STATIC_ROOT` names a local output directory.

4. Create or update the local database tables:

   ```bash
   uv run ./manage.py migrate
   ```

   This writes Django's tables to `../DBs/db.sqlite3`. It does not populate research records or create a Solr index. If startup reports a missing environment setting, check `../.env` against the configuration above. If SQLite cannot open its file, check that `../DBs` exists and is writable.

## Usage

From the `vivo-on-django` checkout, start the local development server:

```bash
uv run ./manage.py runserver 127.0.0.1:8000
```

Open <http://127.0.0.1:8000/> to view the homepage. Informational pages include `/about/`, `/faq/`, and `/help/`. The current `/display/n123/` page uses sample record data; `/display/n123/?format=json` returns that display data as JSON. Stop the server with Ctrl+C.

To render selected searches and profiles from a separately distributed local data bundle, follow [Prepared data for local pages](docs/prepared_data.md). The guide describes mode selection, bundle validation, supported requests, and current limits. Prepared data does not require Solr access.

The local settings write application logs to `../logs/django.log` and use `../cache_dir` for cached responses. Some unfinished routes return placeholder text. Search is not yet connected to Solr, so a successful page response does not demonstrate a working search against real records.

## Tests

From the checkout, after local installation, run all discovered tests:

```bash
uv run ./run_tests.py
```

To run only the Django app tests with each test's name, description, and result:

```bash
uv run ./run_tests.py vivo_app -v
```

The runner uses Django's test framework and creates and removes a test database when needed. Tests use local or sample data and do not contact external data services. Passing the prototype tests does not establish that the Django site reproduces the public Rails site's behavior and appearance or that Solr works.

## Primary dependencies

This inventory compares declarations in [pyproject.toml](pyproject.toml), use in code and configuration, and supporting packages recorded in [uv.lock](uv.lock). No separate requirements file or older Python package declaration is present in this checkout.

### Application packages

| Package | Purpose and evidence |
| --- | --- |
| `Django` | Serves pages, handles URLs, renders templates, and provides database and authentication support. Used throughout [config/](config/) and [vivo_app/](vivo_app/). |
| `python-dotenv` | Loads local environment configuration through `load_dotenv()` in [config/settings.py](config/settings.py). |

The lockfile also records packages these depend on, including Django's `asgiref` and `sqlparse` requirements. These support the directly used packages; their presence in the lockfile does not imply separate application use.

### Development tools and environment requirements

- `django-browser-reload` is declared with the application packages but serves local development. [config/settings.py](config/settings.py) and [config/urls.py](config/urls.py) enable it only when both `DJANGO_DEBUG=True` and `DJANGO_BROWSER_RELOAD=true`.
- Tests use Django's test framework and the standard library's `unittest`; no separate test package is declared. uv manages dependencies and runs commands. [ruff.toml](ruff.toml) contains formatter and linter settings, but Ruff is not declared as a dependency.
- `mysqlclient` is declared in the `staging` and `prod` groups. The checked-in database configuration uses SQLite, so the local setup does not need it. Confirm the intended MySQL configuration before changing those groups.
- Solr is an external service, separate from the Python dependency list. Access to Solr is required for the intended application; supplying and maintaining it remain outside this webapp's current scope.

### Declarations and older code to review

- `trio` is declared directly, but no direct use was found in the current Python code. The visualization tests use `unittest.IsolatedAsyncioTestCase`. Confirm whether another supported execution path needs Trio before removing it or its supporting packages.
- Older account templates, including [profile.html](vivo_app/templates/registration/profile.html) and [change_password.html](vivo_app/templates/registration/change_password.html), load `crispy_forms_tags`. The corresponding package is neither declared nor enabled in Django settings. Confirm whether these pages belong in the agreed public-site scope before deciding how to maintain them.

After sustained confirmation that the required functionality works, review uncertain declarations and development-only packages, retain needed runtime support and environment groups, and prefer `package~=1.2.0` constraints with patch zero where appropriate. Keep exact resolved versions in `uv.lock` and validate each affected dependency group when making those changes.
