/**
 * Teste de UI ponta a ponta: Chromium (Playwright) + controller Python real
 * (tests/ui/devserver.py, input nulo). Uso: node tests/ui/smoke.cjs
 */
const { chromium } = require("playwright");
const { spawn } = require("child_process");
const path = require("path");

const PORT = 8765 + Math.floor(Math.random() * 500);
const BASE = `http://127.0.0.1:${PORT}`;
const results = [];
let page;

function startServer() {
  return new Promise((resolve, reject) => {
    const proc = spawn("python3", [path.join(__dirname, "devserver.py"), String(PORT)], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let out = "";
    const timer = setTimeout(() => reject(new Error("devserver não iniciou: " + out)), 15000);
    proc.stdout.on("data", (chunk) => {
      out += chunk;
      if (out.includes("READY")) {
        clearTimeout(timer);
        resolve(proc);
      }
    });
    proc.stderr.on("data", (chunk) => (out += chunk));
    proc.on("exit", (code) => reject(new Error(`devserver saiu (${code}): ${out}`)));
  });
}

async function api(method, ...args) {
  return page.evaluate(([m, a]) => window.pywebview.api[m](...a), [method, args]);
}
const hook = (...args) => api("__test", ...args);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const errorText = () => page.locator("#errorLabel").innerText();

async function check(name, fn) {
  try {
    await fn();
    results.push([true, name]);
  } catch (err) {
    results.push([false, `${name}\n      ${String(err.message || err).split("\n")[0]}`]);
  }
}
function assert(cond, msg) {
  if (!cond) throw new Error(msg || "assert");
}
async function tab(name) {
  await page.locator(`.tab[data-tab="${name}"]`).click();
}

const TESTS = [];
const test = (name, fn) => TESTS.push([name, fn]);

// --- Fase 1 -----------------------------------------------------------------

test("boot: escolhe idioma e esconde splash", async () => {
  await page.locator(".locale-gate-btn").first().waitFor({ timeout: 8000 });
  await page.locator(".locale-gate-btn", { hasText: "Português" }).click();
  await page.waitForFunction(() => !document.body.classList.contains("booting"));
  await page.waitForFunction(() => document.getElementById("localeGate").hidden);
});

test("erro local não é apagado pelo polling", async () => {
  await tab("profiles");
  await page.fill("#profileName", "");
  await page.locator("#saveProfileBtn").click();
  await sleep(1600);
  assert((await errorText()).length > 5, "mensagem de validação sumiu");
});

test("erro do backend chega traduzido e persiste", async () => {
  await page.fill("#profileName", "CON");
  await page.locator("#saveProfileBtn").click();
  await sleep(1300);
  const text = await errorText();
  assert(/reservado/i.test(text), "esperava erro de nome reservado, veio: " + text);
});

test("perfil com acento salva e aparece na lista", async () => {
  await page.fill("#profileName", "Configuração");
  await page.locator("#saveProfileBtn").click();
  await page.waitForFunction(() =>
    [...document.querySelectorAll("#profileList option")].some((o) => o.value === "Configuração")
  );
  assert((await errorText()) === "", "erro inesperado: " + (await errorText()));
});

test("intervalo: campo vazio não vira 1 ms; valor aplica com debounce", async () => {
  await tab("click");
  await page.fill("#intervalMs", "");
  await sleep(700);
  let st = await api("get_state");
  assert(st.config.interval_ms === 80, "intervalo mudou para " + st.config.interval_ms);
  await page.locator("#intervalMs").pressSequentially("150", { delay: 60 });
  st = await api("get_state");
  assert(st.config.interval_ms === 80, "aplicou antes do debounce: " + st.config.interval_ms);
  await sleep(700);
  st = await api("get_state");
  assert(st.config.interval_ms === 150, "esperava 150, veio " + st.config.interval_ms);
});

test("iniciar/parar pelo botão principal e contador avança", async () => {
  await api("set_config", { interval_ms: 20 });
  await hook("cursor", 5000, 5000); // fora da janela do app
  await page.locator("#mainBtn").click();
  await page.waitForFunction(() => document.getElementById("device").classList.contains("active"));
  await page.waitForFunction(() => parseInt(document.getElementById("counter").textContent, 10) > 3);
  await page.locator("#mainBtn").click();
  await page.waitForFunction(() => !document.getElementById("device").classList.contains("active"));
});

test("fim por limite de cliques atualiza a UI", async () => {
  await api("set_config", { interval_ms: 5, max_clicks: 4 });
  await page.locator("#mainBtn").click();
  await page.waitForFunction(() => document.getElementById("counter").textContent === "000004");
  await page.waitForFunction(() => !document.getElementById("device").classList.contains("active"));
  await api("set_config", { max_clicks: null, interval_ms: 80 });
});

test("lista da sequência não é recriada a cada atualização", async () => {
  await tab("point");
  await api("add_sequence_point", 10, 20, 50);
  await page.locator("#seqList li").first().waitFor();
  await page.evaluate(() => (document.querySelector("#seqList li").dataset.mark = "keep"));
  await sleep(1300);
  const kept = await page.evaluate(() => document.querySelector("#seqList li").dataset.mark);
  assert(kept === "keep", "o item foi recriado");
  await api("clear_sequence");
});

test("script: erro de sintaxe mostra a linha", async () => {
  await tab("advanced").catch(() => {});
  await tab("script");
  await page.fill("#scriptSource", "click\nbogus 1");
  await page.locator("#scriptRunBtn").click();
  await sleep(400);
  assert(/2/.test(await errorText()) && /bogus/.test(await errorText()), await errorText());
});

module.exports = { test, api, hook, sleep, assert, tab, errorText, getPage: () => page };

// Testes das fases seguintes ficam em arquivos separados nesta pasta.
for (const file of require("fs").readdirSync(__dirname).sort()) {
  if (/^phase.*\.cjs$/.test(file)) require(path.join(__dirname, file));
}

(async () => {
  const server = await startServer();
  const browser = await chromium.launch();
  let failed = 0;
  try {
    page = await browser.newPage({ viewport: { width: 468, height: 676 } });
    const consoleErrors = [];
    page.on("pageerror", (err) => consoleErrors.push(String(err)));
    await page.goto(BASE + "/index.html");
    for (const [name, fn] of TESTS) await check(name, fn);
    await check("sem erros de JavaScript no console", async () => {
      assert(consoleErrors.length === 0, consoleErrors.join(" | "));
    });
  } finally {
    await browser.close();
    server.kill();
  }
  for (const [ok, name] of results) {
    if (!ok) failed += 1;
    console.log(`${ok ? "  ok  " : " FAIL "} ${name}`);
  }
  console.log(`\n${results.length - failed}/${results.length} passaram`);
  process.exit(failed ? 1 : 0);
})();
