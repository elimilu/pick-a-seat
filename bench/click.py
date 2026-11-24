"""Measure trusted click timestamp to a frame callback after a paint opportunity."""
import argparse
import json
from math import ceil
import os
import shutil
from statistics import median
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('url', nargs='?', default='http://127.0.0.1:8000')
parser.add_argument('--samples', type=int, default=21)
args = parser.parse_args()
if args.samples < 1:
    parser.error('samples must be positive')

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=os.getenv('CHROMIUM') or shutil.which('chromium'))
    page = browser.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    page.set_default_timeout(15000)
    page_errors, requests = [], []
    page.on('pageerror', lambda e: page_errors.append(str(e)))
    page.on('request', lambda req: requests.append(req.url))
    page.goto(args.url)
    target = page.get_by_role('button', name='Seat B12', exact=True)
    target.wait_for()
    assert target.is_enabled()
    # Exercise show switching independently of the timed, network-free click path.
    for show in ['2', '1']:
        with page.expect_response(lambda r: r.url.endswith('/shows/' + show + '/seats') and r.ok):
            page.locator('#show').select_option(show)
        target.wait_for()
        assert page.locator('#count').inner_text() == '0'
    assert page.locator('#act').inner_text() == 'Neon Atlas'
    assert page.locator('button.seat:disabled').count() > 0
    seat_count = page.locator('button.seat').count()
    requests.clear()
    times, retained = [], []
    for i in range(3 + args.samples):
        page.evaluate('''() => {
          const oldA1 = document.querySelector('[data-seat="A1"]');
          window.sample = new Promise(resolve => {
            document.addEventListener('click', event => {
              const start = event.timeStamp, trusted = event.isTrusted;
              requestAnimationFrame(() => requestAnimationFrame(() => {
                const b = document.querySelector('[data-seat="B12"]');
                resolve({ms: performance.now() - start, trusted,
                  selected: b.getAttribute('aria-pressed'), color: getComputedStyle(b).backgroundColor,
                  count: document.querySelector('#count').textContent, kept: oldA1.isConnected});
              }));
            }, {capture:true, once:true});
          });
        }''')
        target.click()
        sample = page.evaluate('window.sample')
        selected = i % 2 == 0
        assert sample['trusted'] and sample['selected'] == str(selected).lower()
        assert sample['count'] == str(int(selected))
        assert sample['color'] == ('rgb(255, 186, 122)' if selected else 'rgb(59, 102, 92)')
        if i >= 3:
            times.append(round(sample['ms'], 2))
            retained.append(sample['kept'])
    assert not requests, f'Unexpected seat-click requests: {requests}'
    recorded_requests = len(requests)
    if page.locator('#count').inner_text() == '0':
        target.click()
    second = page.locator('button.seat:enabled:not([data-seat="B12"])').first
    second.focus()
    page.keyboard.press('Space')
    assert page.locator('#count').inner_text() == '2'
    assert 'B12' in page.locator('#picks').inner_text()
    page.locator('#show').select_option('2')
    target.wait_for()
    assert page.locator('#count').inner_text() == '0'
    assert target.get_attribute('aria-pressed') == 'false'
    assert not page_errors, page_errors
    print(json.dumps(dict(chromium=browser.version, seats=seat_count, show='Neon Atlas', seat='B12',
                          click_requests=recorded_requests, unrelated_node_retained=sum(retained),
                          median_ms=median(times), p90_ms=sorted(times)[ceil(.9*len(times))-1],
                          samples_ms=times), indent=2))
    browser.close()
