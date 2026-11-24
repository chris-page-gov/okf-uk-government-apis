#!/usr/bin/env node

/** Replay both authored walkthrough-to-Reader journeys against the exact local bundle. */

import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { lstat, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { promisify } from 'node:util';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const BUNDLE = path.join(ROOT, 'bundle');
const CONSUMER_ROOT = path.resolve(process.env.OKF_EXPLORER_ROOT || path.join(ROOT, 'okf-explorer'));
const APP_ROOT = path.join(CONSUMER_ROOT, 'apps', 'okf-explorer');
const BUILD = path.join(APP_ROOT, 'build');
const require = createRequire(path.join(APP_ROOT, 'package.json'));
const { chromium } = require('@playwright/test');
const AxeBuilder = require('@axe-core/playwright');
const OUTPUT = path.resolve(process.argv[2] || 'walkthrough-browser-acceptance.json');
const PORT = Number(process.env.OKF_WALKTHROUGH_PORT || '4294');
const BASE = `http://127.0.0.1:${PORT}`;
const execFileAsync = promisify(execFile);
const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 1000 },
  { name: 'mobile', width: 390, height: 844 }
];
const HTTP_SWEEP_WORKERS = 8;
const MAX_HTTP_ASSET_BYTES = 128 * 1024 * 1024;
const CASES = [
  {
    id: 'core-guide-to-reader',
    guide: 'core-walkthrough.html',
    evidence: 'core-walkthrough-evidence.json',
    descriptor: 'okf-core-explorer.json',
    linkText: 'Open GOV.UK Notify in the core Reader',
    routeKey: 'source_path',
    expectedTitle: 'GOV.UK Notify',
    expectedText: ['Access model: unknown', 'Licence: Not specified', 'Government Digital Service']
  },
  {
    id: 'metadata-guide-to-reader',
    guide: 'notification-catalogue-walkthrough.html',
    evidence: 'notification-walkthrough-evidence.json',
    descriptor: 'okf-explorer.json',
    linkText: 'Open GOV.UK Notify in the metadata Explorer',
    routeKey: 'source_route',
    expectedTitle: 'GOV.UK Notify',
    expectedText: ['Access model', 'unknown', 'Not specified (metadata gap)', 'documentation-only']
  }
];

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function rejectSymlinkPath(root, relative) {
  const decoded = decodeURIComponent(relative).replace(/^\/+/, '');
  assert(decoded && !decoded.includes('\\') && !decoded.split('/').includes('..'), 'unsafe static path');
  const rootInfo = await lstat(root);
  assert(rootInfo.isDirectory() && !rootInfo.isSymbolicLink(), 'static root must be a real directory');
  let current = root;
  const segments = decoded.split('/');
  for (const [index, segment] of segments.entries()) {
    current = path.join(current, segment);
    const info = await lstat(current);
    assert(!info.isSymbolicLink(), 'symbolic links are not served by the acceptance server');
    if (index < segments.length - 1) assert(info.isDirectory(), 'static path parent is not a directory');
    else assert(info.isFile() || info.isDirectory(), 'static target is not a regular file or directory');
  }
  return current;
}

function contentType(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  return ({
    '.css': 'text/css; charset=utf-8', '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8',
    '.jsonld': 'application/ld+json; charset=utf-8', '.svg': 'image/svg+xml',
    '.wasm': 'application/wasm'
  })[extension] || 'application/octet-stream';
}

const checksums = JSON.parse(await readFile(path.join(BUNDLE, 'checksums.json'), 'utf8'));
const bundleIdentity = {
  checksum_manifest_sha256: sha256(await readFile(path.join(BUNDLE, 'checksums.json'))),
  files: Object.keys(checksums.files).length,
  bytes: Object.values(checksums.files).reduce((sum, row) => sum + row.bytes, 0)
};
const appManifestBytes = await readFile(path.join(BUILD, 'okf-explorer-build-manifest.json'));
const appManifest = JSON.parse(appManifestBytes);
const appFiles = new Set(appManifest.materials.map((row) => row.path));
const appPackage = JSON.parse(await readFile(path.join(APP_ROOT, 'package.json'), 'utf8'));
const [{ stdout: consumerCommit }, { stdout: consumerStatus }] = await Promise.all([
  execFileAsync('git', ['-C', CONSUMER_ROOT, 'rev-parse', 'HEAD']),
  execFileAsync('git', ['-C', CONSUMER_ROOT, 'status', '--porcelain'])
]);

const requests = [];
const server = createServer(async (request, response) => {
  const url = new URL(request.url || '/', BASE);
  let root = BUILD;
  let relative = url.pathname.replace(/^\/+/, '') || 'index.html';
  const isBundle = url.pathname.startsWith('/bundle/');
  if (isBundle) {
    root = BUNDLE;
    relative = url.pathname.slice('/bundle/'.length);
  }
  try {
    let filePath = await rejectSymlinkPath(root, relative);
    let stat = await lstat(filePath);
    if (stat.isDirectory()) {
      filePath = await rejectSymlinkPath(root, `${relative.replace(/\/$/, '')}/index.html`);
      stat = await lstat(filePath);
    }
    assert(stat.isFile() && !stat.isSymbolicLink(), 'static entry must be a regular file');
    const rel = path.relative(root, filePath).split(path.sep).join('/');
    const bytes = await readFile(filePath);
    if (isBundle && rel !== 'checksums.json') {
      const expected = checksums.files[rel];
      assert(expected && expected.bytes === bytes.length && expected.sha256 === sha256(bytes), `bundle checksum mismatch: ${rel}`);
    } else if (!isBundle) {
      assert(appFiles.has(rel), `Explorer build manifest does not declare ${rel}`);
    }
    requests.push({ path: url.pathname, status: 200, bytes: bytes.length, sha256: sha256(bytes) });
    response.writeHead(200, {
      'access-control-allow-origin': '*',
      'cache-control': 'no-store',
      'content-length': bytes.length,
      'content-type': contentType(filePath)
    });
    response.end(bytes);
  } catch (error) {
    requests.push({ path: url.pathname, status: 404, error: String(error.message || error) });
    response.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
    response.end('Not found');
  }
});

await new Promise((resolve, reject) => {
  server.once('error', reject);
  server.listen(PORT, '127.0.0.1', resolve);
});

const browser = await chromium.launch({ headless: true });
const report = {
  schema: 'okf-api-walkthrough-browser-acceptance.v1',
  measured_at: new Date().toISOString(),
  status: 'passed',
  bundle: bundleIdentity,
  explorer: {
    version: appPackage.version,
    source_commit: consumerCommit.trim(),
    source_dirty: Boolean(consumerStatus.trim()),
    build_manifest_sha256: sha256(appManifestBytes),
    file_count: appFiles.size
  },
  journeys: [],
  http_asset_sweep: null,
  requests
};

try {
  for (const testCase of CASES) {
    const evidenceBytes = await readFile(path.join(BUNDLE, testCase.evidence));
    const evidence = JSON.parse(evidenceBytes);
    const originalLink = new URL(evidence.reader_url);
    const sourceRoute = evidence.traversal[testCase.routeKey];
    assert(originalLink.hash === `#${sourceRoute}`, `${testCase.id}: Reader link hash differs from its source route`);
    assert(originalLink.searchParams.get('bundle') === evidence.bundle_id, `${testCase.id}: Reader URL points at a different descriptor`);
    const html = await readFile(path.join(BUNDLE, testCase.guide), 'utf8');
    assert(html.includes(testCase.linkText), `${testCase.id}: guide omits the visible Reader link label`);
    for (const source of evidence.sources) {
      assert(html.includes(source.sha256), `${testCase.id}: guide omits a linked source digest`);
      assert(html.includes(source.path), `${testCase.id}: guide omits a linked source path`);
    }

    for (const viewport of VIEWPORTS) {
      const context = await browser.newContext({ viewport: { width: viewport.width, height: viewport.height } });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', (error) => errors.push(`page: ${error.message}`));
      page.on('console', (message) => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });
      const guideUrl = `${BASE}/bundle/${testCase.guide}`;
      await page.route('**/*', async (route) => {
        const requestUrl = new URL(route.request().url());
        if (requestUrl.origin === BASE) {
          await route.continue();
          return;
        }
        if (
          requestUrl.origin === originalLink.origin &&
          requestUrl.pathname === originalLink.pathname &&
          requestUrl.searchParams.get('bundle') === evidence.bundle_id
        ) {
          const local = new URL('/explore/', BASE);
          local.searchParams.set('bundle', `${BASE}/bundle/${testCase.descriptor}`);
          for (const [key, value] of originalLink.searchParams.entries()) {
            if (key !== 'bundle') local.searchParams.set(key, value);
          }
          local.hash = originalLink.hash;
          await route.fulfill({ status: 302, headers: { location: local.toString() } });
          return;
        }
        await route.abort('blockedbyclient');
      });
      await page.goto(guideUrl, { waitUntil: 'domcontentloaded' });
      const guideText = await page.locator('body').innerText();
      for (const negative of evidence.negative_controls) {
        assert(guideText.includes(negative), `${testCase.id}/${viewport.name}: guide omits a negative control`);
      }
      const guideAxe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
      assert(guideAxe.violations.length === 0, `${testCase.id}/${viewport.name}: guide axe violations: ${guideAxe.violations.map((row) => row.id).join(', ')}`);
      const guideScreenshot = `${OUTPUT.replace(/\.json$/i, '')}-${testCase.id}-${viewport.name}-guide.png`;
      await page.screenshot({ path: guideScreenshot, fullPage: true });
      const link = page.getByRole('link', { name: testCase.linkText, exact: true });
      assert(await link.count() === 1, `${testCase.id}/${viewport.name}: expected exactly one visible Reader link`);
      assert(await link.isVisible(), `${testCase.id}/${viewport.name}: Reader link is not visible`);
      const href = await link.getAttribute('href');
      assert(href === evidence.reader_url, `${testCase.id}/${viewport.name}: visible link differs from its evidence URL`);

      await link.click();
      if (viewport.width < 1100) {
        await page.getByRole('button', { name: 'Details', exact: true }).click();
      } else {
        const toggleDetails = page.getByRole('button', { name: 'Toggle details' });
        if (await toggleDetails.getAttribute('aria-expanded') === 'false') await toggleDetails.click();
      }
      try {
        await page.locator('.right-panel h2').filter({ hasText: testCase.expectedTitle }).first().waitFor({ state: 'visible', timeout: 30000 });
      } catch (error) {
        const panelText = await page.locator('.right-panel').innerText().catch(() => '');
        console.error(JSON.stringify({ debug_url: page.url(), right_panel_excerpt: panelText.slice(0, 1200), requests: requests.slice(-12) }));
        throw error;
      }
      assert(new URL(page.url()).pathname === '/explore/', `${testCase.id}/${viewport.name}: clicked link did not reach the local Explorer route`);
      assert(new URL(page.url()).searchParams.get('bundle') === `${BASE}/bundle/${testCase.descriptor}`, `${testCase.id}/${viewport.name}: Reader did not load the expected candidate descriptor`);
      assert(decodeURIComponent(new URL(page.url()).hash.slice(1)) === sourceRoute, `${testCase.id}/${viewport.name}: Reader route differs from the source-bound route`);
      for (const expectedText of testCase.expectedText) {
        assert((await page.locator('.right-panel').innerText()).includes(expectedText), `${testCase.id}/${viewport.name}: Reader panel omits ${expectedText}`);
      }
      const readerAxe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
      assert(readerAxe.violations.length === 0, `${testCase.id}/${viewport.name}: Reader axe violations: ${readerAxe.violations.map((row) => row.id).join(', ')}`);
      assert(errors.length === 0, `${testCase.id}/${viewport.name}: browser errors: ${errors.join('; ')}`);
      const readerScreenshot = `${OUTPUT.replace(/\.json$/i, '')}-${testCase.id}-${viewport.name}-reader.png`;
      await page.screenshot({ path: readerScreenshot, fullPage: true });
      report.journeys.push({
        id: testCase.id,
        viewport: viewport.name,
        status: 'passed',
        guide_path: testCase.guide,
        descriptor_path: testCase.descriptor,
        descriptor_id: evidence.bundle_id,
        descriptor_version: evidence.version,
        snapshot: evidence.snapshot,
        reader_route: sourceRoute,
        guide_sha256: sha256(await readFile(path.join(BUNDLE, testCase.guide))),
        evidence_sha256: sha256(evidenceBytes),
        guide_axe_violations: guideAxe.violations.length,
        reader_axe_violations: readerAxe.violations.length,
        errors,
        guide_screenshot: guideScreenshot,
        reader_screenshot: readerScreenshot
      });
      await context.close();
    }
  }

  const assetRows = Object.entries(checksums.files).sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0);
  const responseRows = new Array(assetRows.length);
  const failures = [];
  let cursor = 0;
  async function verifyNextAsset() {
    while (cursor < assetRows.length) {
      const index = cursor++;
      const [relative, expected] = assetRows[index];
      if (expected.bytes > MAX_HTTP_ASSET_BYTES) {
        failures.push(`${relative}: asset exceeds the bounded HTTP response size`);
        continue;
      }
      const encodedPath = relative.split('/').map(encodeURIComponent).join('/');
      try {
        const response = await fetch(`${BASE}/bundle/${encodedPath}`, { redirect: 'error' });
        if (response.status !== 200) throw new Error(`HTTP ${response.status}`);
        const bytes = Buffer.from(await response.arrayBuffer());
        const digest = sha256(bytes);
        if (bytes.length !== expected.bytes || digest !== expected.sha256) {
          throw new Error(`response identity differs (bytes=${bytes.length}, sha256=${digest})`);
        }
        responseRows[index] = `${relative}\t${bytes.length}\t${digest}\n`;
      } catch (error) {
        failures.push(`${relative}: ${String(error.message || error)}`);
      }
    }
  }
  await Promise.all(Array.from({ length: HTTP_SWEEP_WORKERS }, () => verifyNextAsset()));
  assert(failures.length === 0, `local HTTP asset sweep failed: ${failures.slice(0, 20).join('; ')}`);
  const httpIdentity = responseRows.join('');
  report.http_asset_sweep = {
    status: 'passed',
    files: responseRows.length,
    bytes: assetRows.reduce((sum, [, row]) => sum + row.bytes, 0),
    workers: HTTP_SWEEP_WORKERS,
    response_manifest_sha256: sha256(Buffer.from(httpIdentity, 'utf8')),
    checksum_manifest_sha256: bundleIdentity.checksum_manifest_sha256
  };
} catch (error) {
  report.status = 'failed';
  report.failure = String(error.stack || error);
  report.failure = String(error.stack || error);
  throw error;
} finally {
  report.requests = requests;
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
  const { writeFile, mkdir } = await import('node:fs/promises');
  const outputParent = path.dirname(OUTPUT);
  await mkdir(outputParent, { recursive: true });
  await writeFile(OUTPUT, JSON.stringify(report, null, 2) + '\n', { mode: 0o600 });
}
