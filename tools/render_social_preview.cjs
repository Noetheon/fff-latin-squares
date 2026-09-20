// Optional deterministic layout renderer; Playwright is supplied outside Git.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { createHash } = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const sha = file => createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex');

async function main() {
  const browser = await chromium.launch({headless: true, channel: process.env.BROWSER_CHANNEL || 'chrome'});
  try {
    const page = await browser.newPage({viewport: {width: 1280, height: 640}, deviceScaleFactor: 1});
    await page.goto(pathToFileURL(path.join(root, 'assets/social-preview.html')).href);
    await page.evaluate(() => document.fonts.ready);
    assert(await page.locator('img').evaluate(img => img.complete && img.naturalWidth > 0));
    assert(await page.locator('main').evaluate(el => {
      const box = el.getBoundingClientRect();
      return box.width === 1280 && box.height === 640
        && el.scrollHeight === el.clientHeight && el.scrollWidth === el.clientWidth;
    }));
    const output = 'assets/social-preview.png';
    await page.screenshot({path: path.join(root, output)});
    assert(fs.statSync(path.join(root, output)).size < 1000000);
    const record = {width: 1280, height: 640, browser: browser.version(),
      method: 'HTML/CSS composition with an unaltered public PDF page preview; no generated scientific imagery',
      input_sha256: Object.fromEntries(['assets/social-preview.html', 'assets/compact-cover.png',
        'papers/FFF_Compact_Research_Dossier.pdf'].map(file => [file, sha(file)])),
      output_sha256: sha(output)};
    fs.writeFileSync(path.join(root, 'verification/social-preview-sources.json'), JSON.stringify(record, null, 2) + '\n');
    console.log(JSON.stringify({passed: true, output, bytes: fs.statSync(path.join(root, output)).size}));
  } finally { await browser.close(); }
}
main().catch(error => {console.error(error); process.exitCode = 1;});
