const { test, api, sleep, assert, tab, errorText, getPage } = require("./smoke.cjs");

test("F3: aba Atalhos lista as ações e mostra os combos", async () => {
  const page = getPage();
  await tab("keys");
  assert((await page.locator('.hk-key[data-hk="toggle"]').innerText()) === "F6");
  await api("set_hotkey", "stop_all", "ctrl+alt+f9");
  await page.waitForFunction(
    () => document.querySelector('.hk-key[data-hk="stop_all"]').textContent === "CTRL+ALT+F9"
  );
  assert(!(await page.locator('.hk-clear[data-hk-clear="stop_all"]').isHidden()));
  await page.locator('.hk-clear[data-hk-clear="stop_all"]').click();
  await page.waitForFunction(
    () => document.querySelector('.hk-key[data-hk="stop_all"]').classList.contains("unset")
  );
});

test("F3: clicar no atalho entra em captura e clicar de novo cancela", async () => {
  const page = getPage();
  const key = page.locator('.hk-key[data-hk="pick_point"]');
  await key.click();
  await page.waitForFunction(() =>
    document.querySelector('.hk-key[data-hk="pick_point"]').classList.contains("recording")
  );
  assert((await api("get_state")).recording_hotkey_action === "pick_point");
  await key.click();
  await page.waitForFunction(
    () => !document.querySelector('.hk-key[data-hk="pick_point"]').classList.contains("recording")
  );
});

test("F3: conflito de atalho aparece traduzido", async () => {
  await api("set_hotkey", "stop_all", "F6");
  await sleep(700);
  const text = await errorText();
  assert(/em uso/i.test(text), text);
});

test("F3: modo segurar muda a dica do rodapé", async () => {
  const page = getPage();
  await page.locator('.segmented[data-pref="activation"] .seg[data-val="hold"]').click();
  await page.waitForFunction(() => /segure/i.test(document.getElementById("hotkeyHint").textContent));
  assert((await api("get_state")).settings.activation === "hold");
  await page.locator('.segmented[data-pref="activation"] .seg[data-val="toggle"]').click();
  await page.waitForFunction(() => /iniciar/i.test(document.getElementById("hotkeyHint").textContent));
});
