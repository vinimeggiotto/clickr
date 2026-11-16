const { test, api, sleep, assert, tab, getPage } = require("./smoke.cjs");

test("F2: preferências vêm de settings e não dos perfis", async () => {
  const page = getPage();
  await tab("run");
  await page.locator("#compactMode + .toggle-ui").click();
  await page.waitForFunction(() => document.getElementById("device").classList.contains("compact"));
  let st = await api("get_state");
  assert(st.settings.compact_mode === true, "compact_mode não foi para settings");
  assert(!("compact_mode" in st.config), "compact_mode ainda está na config de clique");
  await api("set_preferences", { compact_mode: false });
  await page.waitForFunction(() => !document.getElementById("device").classList.contains("compact"));
});

test("F2: texto do script é salvo para a próxima sessão", async () => {
  const page = getPage();
  await tab("script");
  await page.fill("#scriptSource", "click 10 20\nwait 5");
  await sleep(1100);
  const settings = await api("get_settings");
  assert(settings.last_script === "click 10 20\nwait 5", "last_script: " + settings.last_script);
});

test("F2: manual marca 'já visto' no backend", async () => {
  await api("set_manual_seen", true);
  assert((await api("get_settings")).manual_seen === true);
});
