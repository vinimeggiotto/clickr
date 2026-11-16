const { test, api, sleep, assert, tab, getPage } = require("./smoke.cjs");

test("F9: opções de sistema ficam na aba Run e persistem", async () => {
  const page = getPage();
  await tab("run");
  assert((await api("get_state")).settings.check_updates === false, "deveria vir desligado");
  assert(await page.locator("#updateBadge").isHidden(), "aviso de versão não deveria aparecer");
  await page.locator("#launchAtLogin + .toggle-ui").scrollIntoViewIfNeeded();
  await page.locator("#launchAtLogin + .toggle-ui").click();
  await sleep(400);
  const st = await api("get_state");
  assert(st.settings.launch_at_login === true, JSON.stringify(st.last_error));
  await api("set_preferences", { launch_at_login: false });
});
