"""
Captures reference pages and compares local pages with an external saved baseline.

Run with uv run -m tools.compare_sites --help. All manifests and output remain outside Git.
"""

import argparse
import html
import json
import re
import shutil
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qsl, urlencode, urlsplit

from PIL import Image, ImageChops, ImageEnhance
from playwright.sync_api import Browser, Page, Request, Response, Route, sync_playwright
from playwright.sync_api import Error as BrowserError

from vivo_app.lib.recorded_responses import external_path, json_object


@dataclass
class Case:
    """Describes one public page, viewport, and sequence of browser actions."""

    id: str
    path: str
    width: int
    height: int
    selectors: dict[str, str]
    actions: list[dict[str, str]] = field(default_factory=list)


@dataclass
class Observations:
    """Collects failed loads and enforces an explicit request limit."""

    origin: str
    local_only: bool
    failures: list[str] = field(default_factory=list)
    requests: int = 0

    def route(self, route: Route) -> None:
        """
        Allows bounded reference loads or requests to the selected local origin only.

        Called by: Playwright route callback
        """
        self.requests += 1
        url = route.request.url
        if self.requests > 150 or (self.local_only and not url.startswith(self.origin + '/')):
            self.failures.append('Blocked resource: ' + normalize_url(url, self.origin))
            route.abort()
        else:
            route.continue_()

    def response(self, response: Response) -> None:
        """
        Records unsuccessful resource responses.

        Called by: Playwright response callback
        """
        if response.status >= 400:
            self.failures.append(f'HTTP {response.status}: {normalize_url(response.url, self.origin)}')

    def failed(self, request: Request) -> None:
        """
        Records failed browser requests without request headers or cookies.

        Called by: Playwright requestfailed callback
        """
        self.failures.append('Failed resource: ' + normalize_url(request.url, self.origin))


def normalize_url(url: str, origin: str) -> str:
    """
    Removes the selected origin and normalizes parameter names while retaining repeated-value order.

    Called by: capture(), Observations callbacks, compare_snapshots()
    """
    parsed = urlsplit(url)
    result = url
    if parsed.netloc == urlsplit(origin).netloc or not parsed.netloc:
        pairs = sorted(parse_qsl(parsed.query, keep_blank_values=True), key=lambda pair: pair[0])
        result = parsed.path + ('?' + urlencode(pairs) if pairs else '') + ('#' + parsed.fragment if parsed.fragment else '')
    return result


def read_cases(path: Path) -> tuple[dict[str, object], list[Case]]:
    """
    Validates an external case manifest and safe output identifiers.

    Called by: run()
    """
    config = json_object(json.loads(external_path(path).read_text()))
    raw_cases = config.get('cases')
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError('The manifest needs a nonempty cases list.')
    cases: list[Case] = []
    seen: set[str] = set()
    for value in raw_cases:
        raw = json_object(value)
        name, route = raw.get('id'), raw.get('path')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', name) or name in seen:
            raise ValueError('Case IDs must be unique simple names.')
        if not isinstance(route, str) or not route.startswith('/') or route.startswith('//'):
            raise ValueError('Case paths must stay on the selected site.')
        width, height = raw.get('width'), raw.get('height')
        if type(width) is not int or type(height) is not int or not 200 <= width <= 3000 or not 200 <= height <= 3000:
            raise ValueError('Case widths and heights must be integers between 200 and 3000.')
        selectors: dict[str, str] = {}
        for key, selector in json_object(raw.get('selectors', {})).items():
            if not isinstance(selector, str):
                raise TypeError('Observation selectors must be text.')
            selectors[key] = selector
        actions: list[dict[str, str]] = []
        raw_actions = raw.get('actions', [])
        if not isinstance(raw_actions, list):
            raise TypeError('Actions must be a list.')
        for item in raw_actions:
            action = json_object(item)
            if action.get('kind') not in {'click', 'navigate', 'fill', 'hover', 'focus', 'press'}:
                raise ValueError('Unsupported browser action.')
            if not all(isinstance(part, str) for part in action.values()):
                raise TypeError('Browser action values must be text.')
            actions.append({key: str(part) for key, part in action.items()})
        seen.add(name)
        cases.append(Case(name, route, width, height, selectors, actions))
    return config, cases


def perform_actions(page: Page, actions: list[dict[str, str]]) -> Response | None:
    """
    Performs only the explicitly listed public browser interactions.

    Called by: capture()
    """
    response = None
    for action in actions:
        locator = page.locator(action['selector']).first
        kind = action['kind']
        if kind == 'navigate':
            with page.expect_navigation(wait_until='networkidle') as navigation:
                locator.click()
            response = navigation.value
        elif kind == 'click':
            locator.click()
        elif kind == 'fill':
            locator.fill(action.get('value', ''))
        elif kind == 'hover':
            locator.hover()
        elif kind == 'focus':
            locator.focus()
        elif kind == 'press':
            locator.press(action['value'])
        if 'wait_for' in action:
            page.locator(action['wait_for']).first.wait_for(state='visible')
    return response


def observe_text(page: Page, selectors: dict[str, str]) -> dict[str, list[str]]:
    """
    Requires every requested observation to find an element before recording its text.

    Called by: capture()
    """
    observations: dict[str, list[str]] = {}
    for name, selector in selectors.items():
        values = page.locator(selector).all_inner_texts()
        if not values:
            raise ValueError('An observation selector found no element: ' + name)
        observations[name] = [' '.join(value.split()) for value in values]
    return observations


def capture(browser: Browser, case: Case, origin: str, output: Path, local_only: bool) -> dict[str, object]:
    """
    Records response details, selected visible text, loaded images, errors, and one viewport screenshot.

    Called by: run()
    """
    observer = Observations(origin, local_only)
    context = browser.new_context(
        viewport={'width': case.width, 'height': case.height},
        device_scale_factor=1,
        locale='en-US',
        timezone_id='America/New_York',
        reduced_motion='reduce',
    )
    context.route('**/*', observer.route)
    page = context.new_page()
    page.set_default_timeout(12000)
    page.set_default_navigation_timeout(30000)
    errors: list[str] = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('response', observer.response)
    page.on('requestfailed', observer.failed)
    snapshot: dict[str, object] = {
        'case': case.id,
        'viewport': [case.width, case.height],
        'browser_version': browser.version,
    }
    try:
        response = page.goto(origin + case.path, wait_until='networkidle')
        if response is None:
            raise ValueError('The navigation produced no HTTP response.')
        if response.status in {401, 403, 429}:
            raise ValueError('Reference access is unavailable or requires interaction; capture stops here.')
        action_response = perform_actions(page, case.actions)
        if action_response is not None:
            response = action_response
        page.wait_for_function('!window.jQuery || window.jQuery(":animated").length === 0')
        page.evaluate('document.fonts.ready')
        page.locator('img').evaluate_all(
            '(items) => Promise.all(items.map(i => i.complete ? Promise.resolve() : new Promise(r => {i.addEventListener("load", r, {once:true}); i.addEventListener("error", r, {once:true});})))'
        )
        snapshot.update(
            status=response.status,
            content_type=response.headers.get('content-type', '').split(';')[0],
            final_url=normalize_url(page.url, origin),
            title=page.title(),
            text=observe_text(page, case.selectors),
            images=page.locator('img').evaluate_all(
                '(items) => items.map(i => ({alt:i.alt, loaded:i.complete && i.naturalWidth > 0}))'
            ),
        )
        page.screenshot(path=str(output / (case.id + '.png')), animations='disabled')
    except (BrowserError, ValueError, OSError) as exc:
        snapshot['capture_error'] = str(exc)
    finally:
        snapshot.update(resource_failures=observer.failures, script_errors=errors, request_count=observer.requests)
        context.close()
    (output / (case.id + '.json')).write_text(json.dumps(snapshot, indent=2) + '\n')
    return snapshot


def compare_snapshots(expected: dict[str, object], actual: dict[str, object]) -> list[str]:
    """
    Reports changed observations and treats incomplete captures or missing assets as failures.

    Called by: run(), self_test(), unit tests
    """
    failures: list[str] = []
    for side, snapshot in [('reference', expected), ('local', actual)]:
        for key in ['capture_error', 'resource_failures', 'script_errors']:
            if snapshot.get(key):
                failures.append(side + ': ' + key)
        images = snapshot.get('images', [])
        if isinstance(images, list) and any(isinstance(image, dict) and not image.get('loaded') for image in images):
            failures.append(side + ': missing image')
    for key in ['viewport', 'status', 'content_type', 'final_url', 'title', 'text', 'images']:
        if key not in expected or key not in actual or expected[key] != actual[key]:
            failures.append('Changed ' + key)
    return failures


def image_difference(expected: Path, actual: Path, output: Path) -> dict[str, object]:
    """
    Saves an amplified difference image and counts pixels that differ in any RGB channel.

    Called by: run(), self_test(), unit tests
    """
    with Image.open(expected) as left_image, Image.open(actual) as right_image:
        left, right = left_image.convert('RGB'), right_image.convert('RGB')
        if left.size != right.size:
            result: dict[str, object] = {'different_size': True, 'changed_ratio': 1.0}
        else:
            difference = ImageChops.difference(left, right)
            red, green, blue = difference.split()
            maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
            unchanged = maximum.histogram()[0]
            changed = left.width * left.height - unchanged
            ImageEnhance.Contrast(difference).enhance(4).save(output)
            result = {
                'different_size': False,
                'changed_pixels': changed,
                'changed_ratio': changed / (left.width * left.height),
                'bounds': difference.getbbox(),
            }
    return result


def write_report(output: Path, report: dict[str, object], rows: list[dict[str, object]]) -> None:
    """
    Writes machine-readable results and a readable report with evidence links.

    Called by: run(), self_test()
    """
    report['cases'] = rows
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    lines = [
        '# Browser comparison report',
        '',
        f'Result: {report["result"]}. Selected cases only; source integration is not verified.',
        '',
        '| Case | Result | Details |',
        '| --- | --- | --- |',
    ]
    for row in rows:
        name = str(row['case'])
        lines.append(f'| {name} | {row["result"]} | {row.get("differences", "")} |')
    lines.extend(
        [
            '',
            'Review each case’s JSON and screenshot. A nonzero pixel difference requires review; this tool does not accept a visual difference automatically.',
            '',
        ]
    )
    for row in rows:
        name = str(row['case'])
        if (output / (name + '.png')).exists():
            lines.append(f'- [{name}: local screenshot]({name}.png), [observations]({name}.json)')
        if (output / (name + '-difference.png')).exists():
            lines.append(f'- [{name}: amplified pixel difference]({name}-difference.png)')
    (output / 'report.md').write_text('\n'.join(lines) + '\n')
    html_rows = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Browser comparison</title><style>body{font-family:sans-serif;margin:24px}section{margin:32px 0}.pair{display:flex;gap:16px}.pair figure{width:50%;margin:0}img{max-width:100%;border:1px solid #ccc}pre{white-space:pre-wrap}</style><h1>Browser comparison</h1><p>Selected cases only. Differences require review; source integration remains unverified.</p>'
    ]
    for row in rows:
        name = str(row['case'])
        html_rows.append(
            '<section><h2>'
            + html.escape(name)
            + '</h2><pre>'
            + html.escape(json.dumps(row, indent=2))
            + '</pre><div class="pair">'
        )
        for suffix, label in [('-reference', 'Saved reference'), ('', 'Current local page')]:
            if (output / (name + suffix + '.png')).exists():
                html_rows.append(
                    f'<figure><figcaption>{label}</figcaption><img src="{name}{suffix}.png" alt="{label}"></figure>'
                )
        html_rows.append('</div></section>')
    (output / 'report.html').write_text('\n'.join(html_rows) + '</html>')


class InventedServer(HTTPServer):
    """Serves one invented comparison variation at a time on loopback."""

    variant: str = 'reference'


class InventedHandler(BaseHTTPRequestHandler):
    """Returns controlled pages and redirects for the detector check."""

    def log_message(self, format: str, *args: object) -> None:
        """
        Keeps the local test server from writing noisy request logs.

        Called by: BaseHTTPRequestHandler
        """

    def do_GET(self) -> None:
        """
        Serves the selected invented page, image, or redirect.

        Called by: HTTPServer request handler
        """
        server = self.server
        assert isinstance(server, InventedServer)
        variant = server.variant
        status, kind = 200, 'text/html'
        location = ''
        if self.path == '/start':
            body = '<!doctype html><title>Start</title><a id="continue" href="/case">Continue</a>'
        elif self.path == '/icon.svg':
            status = 404 if variant == 'missing-asset' else 200
            kind = 'image/svg+xml'
            body = (
                ''
                if status == 404
                else '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20" fill="blue"/></svg>'
            )
        elif variant == 'redirect' and self.path != '/moved':
            status, location, body = 302, '/moved', ''
        else:
            if variant == 'navigation-status':
                status = 201
            heading = 'Changed heading' if variant == 'heading' else 'Invented heading'
            margin = '80px' if variant == 'layout' else '10px'
            kind = 'text/plain' if variant == 'content-type' else 'text/html'
            body = f'<!doctype html><title>Invented comparison</title><h1 style="margin-left:{margin}">{heading}</h1><img src="/icon.svg" alt="Invented icon">'
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body.encode())))
        if location:
            self.send_header('Location', location)
        self.end_headers()
        self.wfile.write(body.encode())


def self_test(browser: Browser, output: Path) -> bool:
    """
    Proves browser observations and pixel comparisons catch deliberate changes and remain stable unchanged.

    Called by: run()
    """
    snapshots: dict[str, dict[str, object]] = {}
    server = InventedServer(('127.0.0.1', 0), InventedHandler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        origin = f'http://127.0.0.1:{server.server_port}'
        for variant in [
            'reference',
            'unchanged',
            'heading',
            'redirect',
            'content-type',
            'missing-asset',
            'layout',
            'missing-observation',
            'navigation-reference',
            'navigation-status',
        ]:
            server.variant = variant
            case = Case(variant, '/case', 800, 600, {'heading': 'h1'})
            if variant == 'missing-observation':
                case.selectors = {'missing': '#absent'}
            if variant.startswith('navigation-'):
                case.path = '/start'
                case.actions = [{'kind': 'navigate', 'selector': '#continue'}]
            snapshots[variant] = capture(browser, case, origin, output, True)
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    rows: list[dict[str, object]] = []
    for variant, snapshot in snapshots.items():
        if variant == 'reference':
            continue
        differences = compare_snapshots(snapshots['reference'], snapshot)
        pixels: dict[str, object] = {'changed_ratio': 1.0, 'screenshot_missing': True}
        if (output / (variant + '.png')).exists():
            pixels = image_difference(
                output / 'reference.png', output / (variant + '.png'), output / (variant + '-difference.png')
            )
        detected = bool(differences) or pixels['changed_ratio'] != 0
        passed = detected == (variant not in {'unchanged', 'navigation-reference'})
        rows.append({'case': variant, 'result': 'pass' if passed else 'fail', 'differences': differences, 'pixels': pixels})
    passed = all(row['result'] == 'pass' for row in rows)
    write_report(
        output,
        {'result': 'pass' if passed else 'fail', 'purpose': 'deliberate-change checks', 'browser_version': browser.version},
        rows,
    )
    return passed


def run(args: argparse.Namespace) -> bool:
    """
    Runs an explicit capture, offline comparison, or invented detector check.

    Called by: main()
    """
    output = external_path(Path(args.output))
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use a new empty output directory; existing evidence is never overwritten.')
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=args.browser_executable)
        if args.mode == 'self-test':
            passed = self_test(browser, output)
        else:
            if not args.manifest:
                raise ValueError('This mode requires --manifest.')
            manifest_path = external_path(Path(args.manifest))
            config, cases = read_cases(manifest_path)
            local = args.mode == 'compare-local'
            origin = str(config.get('local_base_url' if local else 'reference_base_url', '')).rstrip('/')
            parsed = urlsplit(origin)
            if parsed.scheme not in {'http', 'https'} or not parsed.netloc or parsed.path or parsed.username:
                raise ValueError('Configure a plain HTTP(S) site origin.')
            if local and parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}:
                raise ValueError('Offline comparisons require a loopback local site.')
            baseline = external_path(Path(args.baseline)) if args.baseline else None
            if local and baseline is None:
                raise ValueError('compare-local requires --baseline.')
            (output / 'case-manifest.json').write_bytes(manifest_path.read_bytes())
            rows: list[dict[str, object]] = []
            for case in cases:
                actual = capture(browser, case, origin, output, local)
                differences = []
                pixels: dict[str, object] = {}
                if local and baseline is not None:
                    expected = json_object(json.loads((baseline / (case.id + '.json')).read_text()))
                    if (baseline / (case.id + '.png')).exists():
                        shutil.copy2(baseline / (case.id + '.png'), output / (case.id + '-reference.png'))
                    differences = compare_snapshots(expected, actual)
                    if expected.get('browser_version', browser.version) != browser.version:
                        differences.append('Browser version differs from the baseline')
                    if (output / (case.id + '.png')).exists() and (baseline / (case.id + '.png')).exists():
                        pixels = image_difference(
                            baseline / (case.id + '.png'),
                            output / (case.id + '.png'),
                            output / (case.id + '-difference.png'),
                        )
                        if pixels['changed_ratio'] != 0:
                            differences.append('Pixels differ; review required')
                    else:
                        differences.append('Screenshot missing')
                else:
                    differences = compare_snapshots(actual, actual)
                rows.append(
                    {
                        'case': case.id,
                        'result': 'needs_review' if differences else 'pass',
                        'differences': differences,
                        'pixels': pixels,
                    }
                )
                if actual.get('capture_error'):
                    break
                if not local:
                    time.sleep(0.4)
            passed = len(rows) == len(cases) and all(row['result'] == 'pass' for row in rows)
            write_report(
                output,
                {
                    'result': 'pass' if passed else 'needs_review',
                    'mode': args.mode,
                    'data_mode': config.get('data_mode'),
                    'bundle_version': config.get('bundle_version'),
                    'browser_version': browser.version,
                    'required_cases': len(cases),
                    'completed_cases': len(rows),
                },
                rows,
            )
        browser.close()
    return passed


def main() -> None:
    """
    Parses the command and returns failure for incomplete or differing comparisons.

    Called by: module entry point
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['capture-reference', 'compare-local', 'self-test'])
    parser.add_argument('--manifest')
    parser.add_argument('--baseline')
    parser.add_argument('--output', required=True)
    parser.add_argument('--browser-executable', default=None)
    args = parser.parse_args()
    passed = run(args)
    print('Comparison passed.' if passed else 'Comparison needs review; inspect the saved report.')
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
