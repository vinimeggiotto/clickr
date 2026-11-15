const { test, api, hook, sleep, assert, tab, getPage } = require("./smoke.cjs");

test("F5: unidades de tempo convertem para ms e persistem", async () => {
  const page = getPage();
  await tab("run");
  await page.selectOption('.unit-select[data-unit="max_duration"]', "min");
  await page.fill("#maxDuration", "1.5");
  await page.locator("#maxDuration").blur();
  await sleep(300);
  let st = await api("get_state");
  assert(st.config.max_duration_ms === 90000, "max_duration_ms=" + st.config.max_duration_ms);
  assert(st.settings.time_units.max_duration === "min");
  await page.selectOption('.unit-select[data-unit="max_duration"]', "s");
  await page.waitForFunction(() => document.getElementById("maxDuration").value === "90");
  await page.fill("#maxDuration", "");
  await page.locator("#maxDuration").blur();
  await sleep(300);
  st = await api("get_state");
  assert(st.config.max_duration_ms === null, "campo vazio deveria remover o limite");
  await page.selectOption('.unit-select[data-unit="max_duration"]', "ms");
});

test("F5: contagem regressiva, tempo decorrido e CPS real", async () => {
  const page = getPage();
  await hook("cursor", 5000, 5000);
  await api("set_config", { start_delay_ms: 1200, interval_ms: 20 });
  await api("start");
  await page.waitForFunction(() => !document.getElementById("countdown").hidden);
  const shown = parseFloat(await page.locator("#countdown").innerText());
  assert(shown > 0 && shown <= 1.2, "contagem: " + shown);
  await page.waitForFunction(() => document.getElementById("countdown").hidden, null, { timeout: 4000 });
  await sleep(1500);
  const cps = parseFloat(await page.locator("#liveCps").innerText());
  assert(cps > 30 && cps < 60, "cps real: " + cps);
  assert((await page.locator("#liveElapsed").innerText()) !== "00:00", "tempo não avançou");
  await api("stop");
  await api("set_config", { start_delay_ms: 0, interval_ms: 80 });
});

test("F5: sequência — editar delay, reordenar e destacar o passo ativo", async () => {
  const page = getPage();
  await tab("point");
  await api("clear_sequence");
  await page.fill("#fixedX", "11");
  await page.fill("#fixedY", "22");
  await page.locator("#fixedY").blur();
  await page.locator("#addSeqBtn").click();
  await api("add_sequence_point", 33, 44, 500);
  await page.waitForFunction(() => document.querySelectorAll("#seqList li").length === 2);
  assert((await page.locator("#seqList li .xy").first().innerText()) === "11, 22");
  const delay = page.locator("#seqList li").first().locator(".delay input");
  await delay.fill("300");
  await delay.blur();
  await sleep(300);
  let seq = (await api("get_state")).config.sequence;
  assert(seq[0].delay_ms === 300, JSON.stringify(seq));
  await page.locator("#seqList li").first().locator(".ops button").nth(1).click(); // ↓
  await sleep(300);
  seq = (await api("get_state")).config.sequence;
  assert(seq[0].x === 33 && seq[1].x === 11, JSON.stringify(seq));
  await api("start");
  await page.waitForFunction(() => !!document.querySelector("#seqList li.current"));
  await api("stop");
  await api("clear_sequence");
  await api("set_config", { position_mode: "cursor" });
});

test("F5: capturar ponto direto para a sequência", async () => {
  const page = getPage();
  await page.locator("#pickSeqBtn").click();
  await page.waitForFunction(async () => (await window.pywebview.api.get_state()).picking);
  await hook("cursor", 640, 480);
  await api("confirm_pick");
  await page.waitForFunction(() => document.querySelectorAll("#seqList li").length === 1);
  assert((await page.locator("#seqList li .xy").innerText()) === "640, 480");
  await api("clear_sequence");
});

test("F5: 'usar janela atual' mostra contagem e pode ser cancelado", async () => {
  const page = getPage();
  await tab("advanced");
  await page.locator("#wfCaptureBtn").click();
  await page.waitForFunction(() => document.getElementById("wfCaptureBtn").classList.contains("recording"));
  await page.locator("#wfCaptureBtn").click();
  await page.waitForFunction(() => !document.getElementById("wfCaptureBtn").classList.contains("recording"));
});

test("F5: script mostra a linha em execução", async () => {
  const page = getPage();
  await tab("script");
  await page.fill("#scriptSource", "click 1 1\nwait 900\nclick 2 2");
  await page.locator("#scriptRunBtn").click();
  await page.waitForFunction(() => /2/.test(document.getElementById("scriptHint").textContent));
  await api("script_stop");
});

test("F5: status explica quando o clique está sendo pulado", async () => {
  const page = getPage();
  await hook("cursor", 150, 150); // dentro da janela (falsa) do app
  await api("set_config", { interval_ms: 10 });
  await api("start");
  await page.waitForFunction(() => /Clickr/.test(document.getElementById("statusLabel").textContent));
  await hook("cursor", 5000, 5000);
  await page.waitForFunction(() => /ativo/.test(document.getElementById("statusLabel").textContent));
  await api("stop");
  await api("set_config", { interval_ms: 80 });
});
