/**
 * Renders index.html in headless Chrome and checks the arithmetic.
 *
 * The page has no JavaScript, so nothing can assert on its own behaviour from
 * the inside, and every digit on screen is CSS generated content. Generated
 * content is invisible to innerText, so the readout is taken from the
 * accessibility tree, which is both the honest "what the user is told" view
 * and a free check that the answer reaches a screen reader at all.
 *
 *   npm install && npm test
 */
const path = require('path');
const puppeteer = require('puppeteer');

const FILE = 'file:///' + path.join(__dirname, 'index.html').replace(/\\/g, '/');

// [operator id, first number, second number, expected readout]
const CASES = [
  ['p', 0, 0, '0+0=0'],
  ['p', 7, 6, '7+6=13'],
  ['p', 9, 9, '9+9=18'],
  ['n', 7, 6, '7\u22126=1'],
  ['n', 2, 9, '2\u22129=\u22127'],
  ['n', 0, 9, '0\u22129=\u22129'],
  ['m', 7, 6, '7\u00d76=42'],
  ['m', 9, 9, '9\u00d79=81'],
  ['m', 0, 9, '0\u00d79=0'],
  ['d', 8, 2, '8\u00f72=4'],
  ['d', 7, 2, '7\u00f72=3r1'],
  ['d', 5, 2, '5\u00f72=2r1'],
  ['d', 1, 3, '1\u00f73=0r1'],
  ['d', 8, 3, '8\u00f73=2r2'],
  ['d', 9, 9, '9\u00f79=1'],
  ['d', 0, 5, '0\u00f75=0'],
  ['d', 7, 0, '7\u00f70=\u221e'],
  ['e', 2, 3, '2^3=8'],
  ['e', 9, 9, '9^9=387420489'],
  ['e', 5, 0, '5^0=1'],
];

async function readout(page) {
  // Chrome flattens this page's spans, so the readout cannot be snapshotted by
  // rooting at <output>: puppeteer resolves that DOM node to its first
  // StaticText child. Take the whole tree instead and slice the run of text
  // between the heading and the first radio. Column captions are uppercased by
  // text-transform and are the only other text in that run, so drop them; a
  // readout part is never two-or-more capital letters.
  const snap = await page.accessibility.snapshot();
  const flat = [];
  (function walk(node) {
    if (!node) return;
    flat.push(node);
    (node.children || []).forEach(walk);
  })(snap);

  const start = flat.findIndex((n) => n.role === 'heading');
  const end = flat.findIndex((n) => n.role === 'radio');
  if (start < 0 || end < 0 || end <= start) throw new Error('could not locate the readout in the a11y tree');

  return flat
    .slice(start + 1, end)
    .map((n) => n.name || '')
    .filter((s) => !/^[A-Z]{2,}$/.test(s))
    .join('')
    // On exact division the remainder counter falls back to a zero-width
    // space, which is invisible on screen but real in the a11y tree.
    .replace(/[\u200b\s]+/g, '');
}

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.setViewport({ width: 620, height: 820 });
  await page.goto(FILE, { waitUntil: 'load' });

  let failed = 0;
  const fail = (msg) => { console.error('FAIL  ' + msg); failed++; };

  const scripts = await page.$$eval('script', (n) => n.length);
  if (scripts !== 0) fail(`page ships ${scripts} script tag(s)`);

  const favicon = await page.$eval('link[rel="icon"]', (link) => link.href);
  if (!favicon.endsWith('/favicon.svg')) fail(`unexpected favicon URL: ${favicon}`);

  for (const [op, a, b, want] of CASES) {
    await page.click(`label[for=${op}]`);
    await page.click(`label[for=a${a}]`);
    await page.click(`label[for=b${b}]`);
    const got = await readout(page);
    if (got !== want) fail(`${a} ${op} ${b}: got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`);
  }

  // The page must not scroll sideways on a small phone.
  await page.setViewport({ width: 320, height: 820 });
  await page.click('label[for=e]');
  await page.click('label[for=a9]');
  await page.click('label[for=b9]');
  const box = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    client: document.documentElement.clientWidth,
  }));
  if (box.scroll > box.client) fail(`horizontal overflow at 320px: ${box.scroll} > ${box.client}`);

  await browser.close();
  if (failed) {
    console.error(`\n${failed} check(s) failed`);
    process.exit(1);
  }
  console.log(`all ${CASES.length} cases pass, no script tags, no overflow at 320px`);
})();
