// Two players: ACTIONS like page.cjs, each prefixed "A:" or "B:" (or "both:" for both); all:wait:ms waits once
const pw = require('/pw/node_modules/playwright-core');
(async () => {
  const browser = await pw.chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const pages = {};
  for (const n of ['A', 'B']) {
    const ctx = await browser.newContext({ viewport: { width: 1024, height: 768 } });
    const page = await ctx.newPage();
    page.on('pageerror', (e) => console.log(n, 'pageerror', e.message));
    page.on('console', (m) => { if (/error|DBG/i.test(m.text())) console.log(n, m.type(), m.text().slice(0, 200)); });
    await page.goto(process.env.URL);
    pages[n] = page;
  }
  const pt = async (page, fx, fy) => { const r = await page.evaluate(() => { const b = canvas.getBoundingClientRect(); return b.width ? [b.left, b.top, b.width, b.height] : [0, 0, innerWidth, innerHeight]; }); return [r[0] + fx * r[2], r[1] + fy * r[3]]; };
  for (const step of process.env.ACTIONS.split(';')) {
    const c = step.indexOf(':'); const who = step.slice(0, c); const a = step.slice(c + 1);
    const i = a.indexOf(':'), k = i < 0 ? a : a.slice(0, i), v = i < 0 ? '' : a.slice(i + 1);
    const n = v.split(',').map(Number);
    const targets = who === 'both' ? ['A', 'B'] : [who];
    if (who === 'all' && k === 'wait') { await new Promise((r) => setTimeout(r, +v)); continue; }
    await Promise.all(targets.map(async (t) => {
      const page = pages[t];
      if (k === 'wait') await page.waitForTimeout(+v);
      else if (k === 'click') { const [x, y] = await pt(page, n[0], n[1]); await page.mouse.move(x, y, { steps: 5 }); await page.waitForTimeout(150); await page.mouse.click(x, y, { delay: 120 }); }
      else if (k === 'drag') { const [x1, y1] = await pt(page, n[0], n[1]); const [x2, y2] = await pt(page, n[2], n[3]); await page.mouse.move(x1, y1); await page.mouse.down(); await page.mouse.move(x2, y2, { steps: 20 }); await page.waitForTimeout(150); await page.mouse.up(); }
      else if (k === 'key') await page.keyboard.press(v);
      else if (k === 'type') await page.keyboard.type(v, { delay: 80 });
      else if (k === 'shot') await page.screenshot({ path: `/out/${v}-${t}.png` });
      else if (k === 'js') console.log(t, 'js', JSON.stringify(await page.evaluate(v)));
      else if (k === 'waitstart') await page.waitForFunction(() => window.__started, null, { timeout: 180000 });
    }));
  }
  await browser.close();
})();
