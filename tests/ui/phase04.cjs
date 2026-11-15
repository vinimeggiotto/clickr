const { test, api, hook, sleep, assert, tab, getPage } = require("./smoke.cjs");

test("F4: modo TECLA troca os controles e envia teclas", async () => {
  const page = getPage();
  await tab("click");
  await page.locator('.segmented[data-group="action"] .seg[data-val="key"]').click();
  await page.waitForFunction(() => !document.getElementById("keyRow").hidden);
  assert(await page.locator("#mouseButtonRow").isHidden(), "seletor de botão deveria sumir");
  await page.fill("#keyName", "ctrl+e");
  await page.locator("#keyName").blur();
  await page.waitForFunction(() => document.getElementById("keyName").value === "CTRL+E");
  await api("set_config", { interval_ms: 5, max_clicks: 2 });
  await hook("reset_input");
  await api("start");
  await sleep(300);
  const rec = await hook("input");
  assert(rec.filter((c) => c[0] === "key_down" && c[1] === 69).length === 2, JSON.stringify(rec));
  await page.locator('.segmented[data-group="action"] .seg[data-val="mouse"]').click();
  await page.waitForFunction(() => document.getElementById("keyRow").hidden);
  await api("set_config", { interval_ms: 80, max_clicks: null });
});

test("F4: variação de posição e devolver cursor", async () => {
  const page = getPage();
  await tab("point");
  await page.fill("#posJitter", "12");
  await page.locator("#posJitter").blur();
  await page.locator("#restoreCursor + .toggle-ui").click();
  await sleep(300);
  const cfg = (await api("get_state")).config;
  assert(cfg.position_jitter_px === 12 && cfg.restore_cursor === true, JSON.stringify(cfg));
  await api("set_config", { position_jitter_px: 0, restore_cursor: false });
});
