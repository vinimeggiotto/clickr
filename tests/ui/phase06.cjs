const { test, api, hook, sleep, assert, tab, errorText, getPage } = require("./smoke.cjs");

test("F6: macro — salvar, carregar, repetir e excluir com confirmação", async () => {
  const page = getPage();
  await tab("macro");
  // Grava de verdade (listeners são dublês: a macro fica vazia) e injeta eventos via arquivo.
  assert(await page.locator("#macroSaveBtn").isDisabled(), "salvar deveria estar desabilitado sem eventos");
  const dir = await hook("data_dir");
  const fs = require("fs");
  const path = require("path");
  const macros = path.join(dir, "Clickr", "macros");
  fs.mkdirSync(macros, { recursive: true });
  fs.writeFileSync(
    path.join(macros, "Coleta.json"),
    JSON.stringify({
      name: "Coleta",
      version: 1,
      events: [
        { t: 0.0, kind: "mouse_down", x: 7, y: 7, button: "left" },
        { t: 0.02, kind: "mouse_up", x: 7, y: 7, button: "left" },
      ],
    })
  );
  await page.fill("#macroName", "Coleta");
  await page.locator("#macroLoadBtn").click();
  await page.waitForFunction(() => /2 evento/.test(document.getElementById("macroHint").textContent));
  await page.waitForFunction(() => document.querySelectorAll("#macroList option").length === 1);

  await page.fill("#macroRepeat", "3");
  await page.fill("#macroSpeed", "4");
  await page.locator("#macroSpeed").blur();
  await hook("reset_input");
  await page.locator("#macroPlayBtn").click();
  await sleep(600);
  const downs = (await hook("input")).filter((c) => c[0] === "down").length;
  assert(downs === 3, "esperava 3 repetições, veio " + downs);

  await page.fill("#macroName", "Cópia da coleta");
  await page.locator("#macroSaveBtn").click();
  await page.waitForFunction(() => document.querySelectorAll("#macroList option").length === 2);

  await page.selectOption("#macroList", "Coleta");
  await page.locator("#macroDeleteBtn").click();
  await page.waitForFunction(() => !document.getElementById("confirmModal").hidden);
  await page.locator("#confirmModalCancel").click();
  await sleep(200);
  assert((await api("get_settings")).macros.length === 2, "cancelar não deveria excluir");
  await page.locator("#macroDeleteBtn").click();
  await page.locator("#confirmModalOk").click();
  await page.waitForFunction(() => document.querySelectorAll("#macroList option").length === 1);
  assert((await errorText()) === "", await errorText());
});
