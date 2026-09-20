// Optional browser QA. Supply Playwright externally; no browser bundle is shipped.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { createHash } = require('node:crypto');

const root = path.resolve(__dirname, '..');
const output = path.resolve(root, process.argv[2] || '.audit/site');
const url = process.argv[3] || pathToFileURL(path.join(root, 'index.html')).href;
assert(output.startsWith(path.join(root, '.audit') + path.sep));
const digest = file => createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex');

async function main() {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true, channel: process.env.BROWSER_CHANNEL || 'chrome' });
  const records = [];
  try {
    for (const [width, height] of [[320, 720], [360, 800], [390, 844], [640, 450], [768, 1024], [1024, 768], [1440, 1000], [1920, 1080]]) {
      const page = await browser.newPage({ viewport: { width, height }, javaScriptEnabled: false, reducedMotion: 'reduce' });
      const errors = [], requests = [];
      page.on('pageerror', e => errors.push(e.message));
      page.on('request', r => requests.push(r.url()));
      await page.goto(url);
      await page.keyboard.press('Tab');
      assert.equal(await page.locator(':focus').innerText(), 'Skip to content');
      await page.keyboard.press('Enter');
      assert.equal(await page.locator(':focus').getAttribute('id'), 'main');
      await page.locator('nav a[href="#evidence"]').click();
      assert.equal(new URL(page.url()).hash, '#evidence');
      assert(await page.locator('#evidence').evaluate(e => Math.abs(e.getBoundingClientRect().top) < 100));
      for (const summary of ['What this public collection includes', 'Rights and reuse']) {
        const item = page.getByText(summary, { exact: true });
        await item.focus();
        await page.keyboard.press('Enter');
        assert(await item.evaluate(e => e.parentElement.open));
        await page.keyboard.press('Enter');
        assert(!(await item.evaluate(e => e.parentElement.open)));
      }
      const record = await page.evaluate(() => ({
        language: document.documentElement.lang,
        overflow: document.documentElement.scrollWidth > innerWidth,
        images: [...document.images].map(e => ({ source: e.getAttribute('src'), loaded: e.complete && e.naturalWidth > 0 })),
        overflowingText: [...document.querySelectorAll('h1,h2,h3,p,summary,.button,nav,.paper-meta,table,code,samp,.view-results')].filter(e => {
          if (!e.getClientRects().length) return false;
          const box = e.getBoundingClientRect();
          return e.scrollWidth > e.clientWidth + 1 || box.right > innerWidth + 1 || box.left < -1;
        }).map(e => e.tagName + ':' + e.className),
        downloads: [...document.querySelectorAll('a[download]')].map(e => e.getAttribute('href')),
        inlineScripts: document.scripts.length,
      }));
      await page.locator('.brand').click();
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: path.join(output, `page-${width}.png`), fullPage: true });
      await page.screenshot({ path: path.join(output, `viewport-${width}.png`) });
      const externalRequests = requests.filter(request => new URL(request).origin !== new URL(url).origin);
      assert.equal(record.language, 'en');
      assert.equal(record.overflow, false);
      assert.deepEqual(record.overflowingText, []);
      assert(record.images.every(i => i.loaded));
      assert.equal(record.downloads.length, 3);
      assert(record.downloads.includes('examples/order8_fff.json'));
      assert.equal(record.inlineScripts, 0);
      assert.deepEqual(errors, []);
      assert.deepEqual(externalRequests, []);
      records.push({ viewport: { width, height }, ...record, keyboardSkipLink: true,
        keyboardDisclosureToggles: true, navigationAnchor: true,
        worksWithoutJavaScript: true, externalRequests: 0, errors });
      await page.close();
    }
    const report = { passed: true, browser: browser.version(),
      target: new URL(url).protocol === 'file:' ? 'local-static-page' : 'published-page',
      page_sha256: digest('index.html'), css_sha256: digest('assets/site.css'),
      pdf_sha256: Object.fromEntries(['FFF_Compact_Research_Dossier.pdf', 'FFF_Long_Research_Dossier.pdf'].map(f => [f, digest('papers/' + f)])),
      records };
    fs.writeFileSync(path.join(output, 'site-checks.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify({ passed: true, viewports: records.length, browser: report.browser }));
  } finally {
    await browser.close();
  }
}
main().catch(e => { console.error(e); process.exitCode = 1; });
