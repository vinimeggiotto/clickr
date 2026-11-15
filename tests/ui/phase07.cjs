const { test, api, hook, sleep, assert, tab, errorText, getPage } = require("./smoke.cjs");

test("F7: script com comandos novos roda pela UI", async () => {
  const page = getPage();
  await tab("script");
  const box = await page.locator("#scriptSource").boundingBox();
  assert(box.height >= 140, "editor pequeno: " + box.height);
  await page.locator("#scriptHelpBtn").click();
  assert(!(await page.locator("#scriptHelp").isHidden()), "ajuda não abriu");
  await page.locator("#scriptHelpBtn").click();
  await hook("reset_input");
  await page.fill("#scriptSource", 'dclick 3 4\nkey CTRL+C\ntype "olá"\nscroll -1\nwait 5-10\ndrag 0 0 20 20');
  await page.locator("#scriptRunBtn").click();
  await sleep(900);
  const rec = await hook("input");
  const has = (entry) => rec.some((c) => JSON.stringify(c) === JSON.stringify(entry));
  assert(has(["type", "olá"]) && has(["scroll", -1, 0]) && has(["move", 20, 20]), JSON.stringify(rec));
  assert((await errorText()) === "", await errorText());
});
