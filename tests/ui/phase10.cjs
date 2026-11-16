const { test, api, sleep, assert, tab, getPage } = require("./smoke.cjs");

test("F10: abas navegáveis por setas e com ARIA coerente", async () => {
  const page = getPage();
  await tab("click");
  await page.locator('.tab[data-tab="click"]').focus();
  await page.keyboard.press("ArrowDown");
  assert(await page.evaluate(() => document.activeElement.dataset.tab) === "run", "seta não moveu o foco");
  assert(!(await page.locator("#panel-run").isHidden()), "painel não acompanhou");
  await page.keyboard.press("End");
  assert(await page.evaluate(() => document.activeElement.dataset.tab) === "schedule");
  await page.keyboard.press("Home");
  const info = await page.evaluate(() => ({
    active: document.activeElement.dataset.tab,
    tabbable: [...document.querySelectorAll(".tab")].filter((t) => t.tabIndex === 0).length,
    selected: document.querySelectorAll('.tab[aria-selected="true"]').length,
    controls: document.activeElement.getAttribute("aria-controls"),
    labelled: document.getElementById("panel-click").getAttribute("aria-labelledby"),
  }));
  assert(info.active === "click" && info.tabbable === 1 && info.selected === 1, JSON.stringify(info));
  assert(info.controls === "panel-click" && info.labelled === "tab-click", JSON.stringify(info));
});

test("F10: botões do mouse têm nome acessível e aria-pressed", async () => {
  const page = getPage();
  const left = page.locator('.segmented[data-group="button"] .seg[data-val="left"]');
  assert(/esquerdo/i.test(await left.getAttribute("aria-label")), "sem aria-label traduzido");
  await page.locator('.segmented[data-group="button"] .seg[data-val="right"]').click();
  await sleep(300);
  assert((await left.getAttribute("aria-pressed")) === "false");
  assert(
    (await page.locator('.segmented[data-group="button"] .seg[data-val="right"]').getAttribute("aria-pressed")) === "true"
  );
  await left.click();
});

test("F10: nenhum texto visível abaixo de 11 px", async () => {
  const page = getPage();
  const small = [];
  for (const name of ["click", "run", "point", "profiles", "keys", "advanced", "macro", "script", "schedule"]) {
    await tab(name);
    const found = await page.evaluate(() => {
      const out = [];
      document.querySelectorAll("body *").forEach((el) => {
        if (!el.offsetParent || !el.childNodes.length) return;
        const hasText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
        if (!hasText) return;
        const size = parseFloat(getComputedStyle(el).fontSize);
        if (size < 11) out.push(`${el.tagName}.${el.className}:${size}`);
      });
      return out;
    });
    small.push(...found);
  }
  assert(small.length === 0, [...new Set(small)].slice(0, 6).join(" | "));
});

test("F10: versão 1.1.0 no rodapé", async () => {
  const page = getPage();
  assert((await page.locator("#appVersion").innerText()) === "v1.1.0");
  assert((await api("get_settings")).version === "1.1.0");
});
