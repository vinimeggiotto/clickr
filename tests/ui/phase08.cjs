const { test, api, hook, sleep, assert, tab, errorText, getPage } = require("./smoke.cjs");

test("F8: perfis — sobrescrever pede confirmação; renomear e excluir", async () => {
  const page = getPage();
  await tab("profiles");
  await page.fill("#profileName", "base");
  await page.locator("#saveProfileBtn").click();
  await page.waitForFunction(() =>
    [...document.querySelectorAll("#profileList option")].some((o) => o.value === "base")
  );
  await api("set_config", { interval_ms: 222 });
  await page.fill("#profileName", "base");
  await page.locator("#saveProfileBtn").click();
  await page.waitForFunction(() => !document.getElementById("confirmModal").hidden);
  await page.locator("#confirmModalCancel").click();
  await sleep(200);
  let saved = await api("load_profile", "base");
  assert(saved.config.interval_ms !== 222, "cancelar não deveria gravar");

  await page.selectOption("#profileList", "base");
  await page.fill("#profileName", "renomeado");
  await page.locator("#renameProfileBtn").click();
  await page.waitForFunction(() =>
    [...document.querySelectorAll("#profileList option")].some((o) => o.value === "renomeado")
  );
  const names = () => page.$$eval("#profileList option", (els) => els.map((o) => o.value));
  assert(!(await names()).includes("base"), "nome antigo continua na lista");

  await page.selectOption("#profileList", "renomeado");
  await page.locator("#deleteProfileBtn").click();
  await page.waitForFunction(() => !document.getElementById("confirmModal").hidden);
  await page.locator("#confirmModalOk").click();
  await page.waitForFunction(
    () => ![...document.querySelectorAll("#profileList option")].some((o) => o.value === "renomeado")
  );
  assert((await errorText()) === "", await errorText());
  await api("set_config", { interval_ms: 80 });
});

test("F8: agenda — recorrência, alvo e resumo", async () => {
  const page = getPage();
  await tab("schedule");
  await page.fill("#scheduleAt", "2999-01-01T08:30");
  await page.locator('#scheduleRepeat .seg[data-val="interval"]').click();
  assert(!(await page.locator("#scheduleIntervalRow").isHidden()), "campo de intervalo oculto");
  await page.fill("#scheduleEvery", "2");
  await page.selectOption("#scheduleEveryUnit", "h");
  await page.selectOption("#scheduleTarget", "script");
  await page.locator("#scheduleSetBtn").click();
  await page.waitForFunction(() => /2999-01-01 08:30/.test(document.getElementById("scheduleHint").textContent));
  const hint = await page.locator("#scheduleHint").innerText();
  assert(/script/i.test(hint) && /2 h/.test(hint), hint);
  const st = await api("get_state");
  assert(st.schedule.interval_s === 7200 && st.schedule.target === "script", JSON.stringify(st.schedule));
  await page.locator("#scheduleCancelBtn").click();
  await page.waitForFunction(() => document.getElementById("scheduleCancelBtn").disabled);

  await page.selectOption("#scheduleTarget", "profile");
  assert(!(await page.locator("#scheduleProfileRow").isHidden()), "seletor de perfil oculto");
  await page.selectOption("#scheduleTarget", "engine");
  await page.locator('#scheduleRepeat .seg[data-val="once"]').click();
});
