(() => {
  const device = document.getElementById("device");
  const mainBtn = document.getElementById("mainBtn");
  const icon = document.getElementById("icon");
  const counterEl = document.getElementById("counter");
  const statusLabel = document.getElementById("statusLabel");
  const intervalMs = document.getElementById("intervalMs");
  const intervalSlider = document.getElementById("intervalSlider");
  const cpsVal = document.getElementById("cpsVal");
  const strip = document.getElementById("strip");
  const fixedHint = document.getElementById("fixedHint");
  const errorLabel = document.getElementById("errorLabel");
  const startDelay = document.getElementById("startDelay");
  const jitterMs = document.getElementById("jitterMs");
  const maxClicks = document.getElementById("maxClicks");
  const maxDuration = document.getElementById("maxDuration");
  const alwaysOnTop = document.getElementById("alwaysOnTop");
  const fixedX = document.getElementById("fixedX");
  const fixedY = document.getElementById("fixedY");
  const pickBtn = document.getElementById("pickBtn");
  const hotkeyBtn = document.getElementById("hotkeyBtn");
  const hotkeyHint = document.getElementById("hotkeyHint");
  const profileName = document.getElementById("profileName");
  const profileList = document.getElementById("profileList");
  const saveProfileBtn = document.getElementById("saveProfileBtn");
  const loadProfileBtn = document.getElementById("loadProfileBtn");
  const exportProfileBtn = document.getElementById("exportProfileBtn");
  const importProfileBtn = document.getElementById("importProfileBtn");
  const wfEnabled = document.getElementById("wfEnabled");
  const wfProcess = document.getElementById("wfProcess");
  const wfTitle = document.getElementById("wfTitle");
  const burstCount = document.getElementById("burstCount");
  const burstPause = document.getElementById("burstPause");
  const seqList = document.getElementById("seqList");
  const seqHint = document.getElementById("seqHint");
  const seqDelay = document.getElementById("seqDelay");
  const addSeqBtn = document.getElementById("addSeqBtn");
  const clearSeqBtn = document.getElementById("clearSeqBtn");
  const compactMode = document.getElementById("compactMode");
  const macroHint = document.getElementById("macroHint");
  const macroRecordBtn = document.getElementById("macroRecordBtn");
  const macroPlayBtn = document.getElementById("macroPlayBtn");
  const macroStopBtn = document.getElementById("macroStopBtn");
  const macroClearBtn = document.getElementById("macroClearBtn");
  const scriptSource = document.getElementById("scriptSource");
  const scriptRunBtn = document.getElementById("scriptRunBtn");
  const scriptStopBtn = document.getElementById("scriptStopBtn");
  const scheduleAt = document.getElementById("scheduleAt");
  const scheduleHint = document.getElementById("scheduleHint");
  const scheduleSetBtn = document.getElementById("scheduleSetBtn");
  const scheduleCancelBtn = document.getElementById("scheduleCancelBtn");

  for (let i = 0; i < 16; i++) {
    strip.appendChild(document.createElement("span"));
  }
  const bars = [...strip.children];
  let barIndex = 0;
  let lastCount = 0;
  let pollTimer = null;
  let apiReady = false;
  let applying = false;
  let toggling = false;
  let stateError = "";
  let localError = "";
  let localErrorTimer = null;
  let intervalTimer = null;
  let lastSequenceKey = null;
  let lastProfilesKey = null;

  const POLL_MS = 500;
  const LOCAL_ERROR_MS = 8000;
  const INTERVAL_DEBOUNCE_MS = 400;

  const localConfig = {
    interval_ms: 80,
    jitter_ms: 0,
    button: "left",
    click_type: "single",
    position_mode: "cursor",
    fixed_x: 0,
    fixed_y: 0,
    hold: false,
    start_delay_ms: 0,
    max_clicks: null,
    max_duration_ms: null,
    burst_count: null,
    burst_pause_ms: null,
    sequence: [],
    window_filter: { enabled: false, process: "", title_contains: "" },
    hotkey: "F6",
    always_on_top: true,
    compact_mode: false,
  };

  function syncCps() {
    const ms = Math.max(1, parseInt(intervalMs.value || "1", 10));
    cpsVal.textContent = (1000 / ms).toFixed(1);
  }

  function api() {
    return window.pywebview && window.pywebview.api ? window.pywebview.api : null;
  }

  function t(key, vars) {
    return window.ClickrI18n ? window.ClickrI18n.t(key, vars) : key;
  }

  async function waitApi(timeoutMs = 5000) {
    const start = Date.now();
    while (!api()) {
      if (Date.now() - start > timeoutMs) {
        throw new Error(t("errors.bridgeUnavailable"));
      }
      await new Promise((r) => setTimeout(r, 50));
    }
    apiReady = true;
  }

  function parseOptionalInt(input) {
    const raw = (input.value || "").trim();
    if (raw === "") return null;
    const n = parseInt(raw, 10);
    if (!Number.isFinite(n) || n <= 0) return null;
    return n;
  }

  function parseOptionalNonNeg(input) {
    const raw = (input.value || "").trim();
    if (raw === "") return null;
    const n = parseInt(raw, 10);
    if (!Number.isFinite(n) || n < 0) return null;
    return n;
  }

  /** Erro vindo do backend: {code, message, params} | string | null → texto. */
  function formatError(err) {
    if (!err) return "";
    if (typeof err === "string") return err;
    if (!err.code || err.code === "generic") return err.message || "";
    const key = "errors." + err.code;
    const text = t(key, err.params || {});
    if (typeof text === "string" && text !== key) return text;
    return err.message || String(err.code || "");
  }

  function renderError() {
    errorLabel.textContent = localError || stateError || "";
  }

  /**
   * Mensagem gerada na própria UI (validação, exceção da bridge, aviso do
   * assistente). Não é apagada pelas atualizações de estado: some sozinha
   * depois de alguns segundos ou quando outra mensagem a substitui.
   */
  function showLocalError(message) {
    localError = message ? String(message) : "";
    if (localErrorTimer) {
      clearTimeout(localErrorTimer);
      localErrorTimer = null;
    }
    if (localError) {
      localErrorTimer = setTimeout(() => {
        localError = "";
        localErrorTimer = null;
        renderError();
      }, LOCAL_ERROR_MS);
    }
    renderError();
  }

  function clearLocalError() {
    showLocalError("");
  }

  /**
   * Chama um método da bridge. Se o retorno for um estado, aplica na UI.
   * Exceções da bridge viram mensagem local; retorna null nesse caso.
   */
  async function call(method, ...args) {
    const bridge = api();
    if (!bridge || typeof bridge[method] !== "function") return null;
    try {
      const result = await bridge[method](...args);
      if (result && typeof result === "object" && result.config) {
        clearLocalError();
        applyVisual(result);
      }
      return result;
    } catch (err) {
      showLocalError(String((err && err.message) || err));
      return null;
    }
  }

  function isFocused(...els) {
    return els.some((el) => document.activeElement === el);
  }

  function renderSequence(sequence, force) {
    const steps = Array.isArray(sequence) ? sequence : [];
    const key = JSON.stringify(steps);
    if (!force && key === lastSequenceKey) return;
    lastSequenceKey = key;
    seqList.innerHTML = "";
    steps.forEach((step, index) => {
      const li = document.createElement("li");
      li.className = "seq-item";
      const info = document.createElement("div");
      info.innerHTML =
        `#${index + 1}  ${step.x}, ${step.y}` +
        `<div class="meta">${t("point.seqDelayMeta", { ms: step.delay_ms || 0 })}</div>`;
      const rm = document.createElement("button");
      rm.type = "button";
      rm.className = "rm";
      rm.title = t("point.seqRemove");
      rm.textContent = "×";
      rm.addEventListener("click", () => call("remove_sequence_point", index));
      li.appendChild(info);
      li.appendChild(rm);
      seqList.appendChild(li);
    });
    seqHint.textContent = steps.length
      ? t("point.seqCount", { n: steps.length })
      : t("point.seqEmpty");
  }

  function applyCompactMode(enabled) {
    device.classList.toggle("compact", !!enabled);
    const hiddenTabs = document.querySelectorAll(".tab-adv");
    hiddenTabs.forEach((tab) => {
      tab.hidden = !!enabled;
    });
    if (enabled) {
      const activeAdv = document.querySelector(".tab-adv.active");
      if (activeAdv) activateTab("click");
    }
  }

  function applyVisual(state) {
    const macro = state.macro || {};
    const script = state.script || {};
    const schedule = state.schedule || {};
    const engineRunning = !!state.running;
    const busy =
      engineRunning || !!macro.playing || !!script.running || !!macro.recording;
    const count = state.click_count || 0;

    device.classList.toggle("active", busy);
    icon.innerHTML = busy ? "&#9632;" : "&#9654;";
    let statusText = t("status.stopped");
    if (macro.recording) statusText = t("status.recording");
    else if (macro.playing) statusText = t("status.macro");
    else if (script.running) statusText = t("status.script");
    else if (engineRunning) statusText = t("status.active");
    statusLabel.textContent = statusText;
    mainBtn.setAttribute("aria-pressed", busy ? "true" : "false");
    counterEl.textContent = String(count).padStart(6, "0");

    if (count > lastCount) {
      bars.forEach((b) => b.classList.remove("hit"));
      bars[barIndex].classList.add("hit");
      barIndex = (barIndex + 1) % bars.length;
    }
    if (!busy) {
      bars.forEach((b) => b.classList.remove("hit"));
    }
    lastCount = count;

    stateError = formatError(state.last_error);
    renderError();

    const recording = !!state.recording_hotkey;
    hotkeyBtn.classList.toggle("recording", recording);
    hotkeyHint.textContent = recording ? t("footer.hotkeyRecording") : t("footer.hotkeyHint");
    pickBtn.disabled = !!state.picking;
    pickBtn.textContent = state.picking ? t("point.picking") : t("point.pick");

    const evCount = macro.event_count || 0;
    macroRecordBtn.dataset.recording = macro.recording ? "1" : "0";
    if (macro.recording) {
      macroHint.textContent = t("macro.recording", { n: evCount });
      macroRecordBtn.textContent = t("macro.stopRecord");
    } else {
      macroHint.textContent = evCount
        ? t("macro.count", { n: evCount })
        : t("macro.empty");
      macroRecordBtn.textContent = t("macro.record");
    }
    macroPlayBtn.disabled = !!macro.recording || evCount === 0;
    macroClearBtn.disabled = !!macro.recording || !!macro.playing;

    if (schedule.active && schedule.at) {
      scheduleHint.textContent = t("schedule.active", {
        at: schedule.at.replace("T", " "),
      });
    } else {
      scheduleHint.textContent = t("schedule.none");
    }

    if (Array.isArray(state.profiles)) {
      refreshProfileList(state.profiles);
    }

    if (state.config) {
      applying = true;
      const cfg = state.config;
      const wf = cfg.window_filter || {};
      Object.assign(localConfig, {
        interval_ms: cfg.interval_ms,
        jitter_ms: cfg.jitter_ms || 0,
        button: cfg.button,
        click_type: cfg.click_type,
        position_mode: cfg.position_mode,
        fixed_x: cfg.fixed_x,
        fixed_y: cfg.fixed_y,
        hold: !!cfg.hold,
        start_delay_ms: cfg.start_delay_ms || 0,
        max_clicks: cfg.max_clicks == null ? null : cfg.max_clicks,
        max_duration_ms: cfg.max_duration_ms == null ? null : cfg.max_duration_ms,
        burst_count: cfg.burst_count == null ? null : cfg.burst_count,
        burst_pause_ms: cfg.burst_pause_ms == null ? null : cfg.burst_pause_ms,
        sequence: Array.isArray(cfg.sequence) ? cfg.sequence : [],
        window_filter: {
          enabled: !!wf.enabled,
          process: wf.process || "",
          title_contains: wf.title_contains || "",
        },
        hotkey: cfg.hotkey || "F6",
        always_on_top: cfg.always_on_top !== false,
        compact_mode: !!cfg.compact_mode,
      });
      applyCompactMode(localConfig.compact_mode);

      if (!isFocused(intervalMs, intervalSlider)) {
        intervalMs.value = String(cfg.interval_ms);
        intervalSlider.value = String(Math.min(500, Math.max(10, cfg.interval_ms)));
        syncCps();
      }
      if (!isFocused(startDelay)) {
        startDelay.value = String(localConfig.start_delay_ms);
      }
      if (!isFocused(jitterMs)) {
        jitterMs.value = String(localConfig.jitter_ms);
      }
      if (!isFocused(maxClicks)) {
        maxClicks.value = localConfig.max_clicks == null ? "" : String(localConfig.max_clicks);
      }
      if (!isFocused(maxDuration)) {
        maxDuration.value =
          localConfig.max_duration_ms == null ? "" : String(localConfig.max_duration_ms);
      }
      if (!isFocused(fixedX)) fixedX.value = String(localConfig.fixed_x);
      if (!isFocused(fixedY)) fixedY.value = String(localConfig.fixed_y);
      if (!isFocused(alwaysOnTop)) alwaysOnTop.checked = localConfig.always_on_top;
      if (!isFocused(compactMode)) compactMode.checked = localConfig.compact_mode;
      if (!isFocused(wfEnabled)) wfEnabled.checked = localConfig.window_filter.enabled;
      if (!isFocused(wfProcess)) wfProcess.value = localConfig.window_filter.process;
      if (!isFocused(wfTitle)) wfTitle.value = localConfig.window_filter.title_contains;
      if (!isFocused(burstCount)) {
        burstCount.value =
          localConfig.burst_count == null ? "" : String(localConfig.burst_count);
      }
      if (!isFocused(burstPause)) {
        burstPause.value =
          localConfig.burst_pause_ms == null ? "" : String(localConfig.burst_pause_ms);
      }

      hotkeyBtn.textContent = localConfig.hotkey;
      setSegmentActive("button", cfg.button);
      setSegmentActive(
        "click_type",
        cfg.click_type === "hold" || cfg.hold ? "hold" : cfg.click_type
      );
      setSegmentActive("position_mode", cfg.position_mode);
      updateFixedHint();
      renderSequence(localConfig.sequence);
      applying = false;
    }
  }

  function refreshProfileList(names) {
    const key = JSON.stringify(names);
    if (key === lastProfilesKey) return;
    lastProfilesKey = key;
    const selected = profileList.value;
    profileList.innerHTML = "";
    names.forEach((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      profileList.appendChild(opt);
    });
    if (selected && names.includes(selected)) {
      profileList.value = selected;
    }
  }

  function setSegmentActive(group, value) {
    const el = document.querySelector(`.segmented[data-group="${group}"]`);
    if (!el) return;
    el.querySelectorAll(".seg").forEach((s) => {
      s.classList.toggle("active", s.dataset.val === value);
    });
  }

  function updateFixedHint() {
    if (localConfig.position_mode === "fixed") {
      fixedHint.innerHTML = t("point.fixedPoint", {
        x: localConfig.fixed_x,
        y: localConfig.fixed_y,
      });
    } else {
      fixedHint.textContent = t("point.fixedHintCursor");
    }
  }

  async function pushConfig(partial) {
    if (applying) return;
    Object.assign(localConfig, partial);
    await call("set_config", partial);
  }

  async function pushWindowFilter(partial) {
    const next = { ...localConfig.window_filter, ...partial };
    localConfig.window_filter = next;
    await pushConfig({ window_filter: next });
  }

  async function refreshState() {
    const bridge = api();
    if (!bridge) return;
    try {
      applyVisual(await bridge.get_state());
    } catch (_) {
      /* bridge ocupada ou encerrando: o próximo ciclo tenta de novo */
    }
  }

  // O backend envia o estado pronto (com limite de frequência); sem argumento,
  // a UI busca por conta própria.
  window.__clickrApplyState = (state) => {
    if (state && typeof state === "object") applyVisual(state);
    else refreshState();
  };

  function startPolling() {
    if (pollTimer) return;
    pollTimer = setInterval(refreshState, POLL_MS);
  }

  function stopPolling() {
    if (!pollTimer) return;
    clearInterval(pollTimer);
    pollTimer = null;
  }

  async function toggleRun() {
    if (toggling) return;
    toggling = true;
    try {
      const bridge = api();
      if (!bridge) return;
      const state = await bridge.get_state();
      const macro = state.macro || {};
      const script = state.script || {};
      if (macro.recording) await call("macro_record_stop");
      else if (macro.playing) await call("macro_stop");
      else if (script.running) await call("script_stop");
      else if (state.running) await call("stop");
      else await call("start");
    } catch (err) {
      showLocalError(String((err && err.message) || err));
    } finally {
      toggling = false;
    }
  }

  function activateTab(name) {
    document.querySelectorAll(".tab").forEach((tab) => {
      const on = tab.dataset.tab === name;
      tab.classList.toggle("active", on);
      tab.setAttribute("aria-selected", on ? "true" : "false");
    });
    document.querySelectorAll(".panel").forEach((panel) => {
      const on = panel.id === `panel-${name}`;
      panel.classList.toggle("active", on);
      panel.hidden = !on;
    });
  }

  /** Lê o intervalo digitado; null se vazio ou inválido (nada é enviado). */
  function readInterval(el) {
    const raw = String(el.value || "").trim();
    if (raw === "") return null;
    const n = parseInt(raw, 10);
    if (!Number.isFinite(n) || n < 1) return null;
    return n;
  }

  function commitInterval(el) {
    if (intervalTimer) {
      clearTimeout(intervalTimer);
      intervalTimer = null;
    }
    const ms = readInterval(el);
    if (ms == null) {
      // Campo vazio/inválido: mantém o valor em vigor.
      intervalMs.value = String(localConfig.interval_ms);
      syncCps();
      return;
    }
    if (ms !== localConfig.interval_ms) pushConfig({ interval_ms: ms });
  }

  function scheduleInterval(el) {
    if (intervalTimer) clearTimeout(intervalTimer);
    if (readInterval(el) == null) return;
    intervalTimer = setTimeout(() => commitInterval(el), INTERVAL_DEBOUNCE_MS);
  }

  intervalMs.addEventListener("input", () => {
    if (readInterval(intervalMs) != null) {
      intervalSlider.value = intervalMs.value;
      syncCps();
    }
    scheduleInterval(intervalMs);
  });
  intervalMs.addEventListener("change", () => commitInterval(intervalMs));

  intervalSlider.addEventListener("input", () => {
    intervalMs.value = intervalSlider.value;
    syncCps();
    scheduleInterval(intervalSlider);
  });
  intervalSlider.addEventListener("change", () => commitInterval(intervalSlider));
  syncCps();

  startDelay.addEventListener("change", () => {
    const ms = Math.max(0, parseInt(startDelay.value || "0", 10) || 0);
    startDelay.value = String(ms);
    pushConfig({ start_delay_ms: ms });
  });

  jitterMs.addEventListener("change", () => {
    const ms = Math.max(0, parseInt(jitterMs.value || "0", 10) || 0);
    jitterMs.value = String(ms);
    pushConfig({ jitter_ms: ms });
  });

  maxClicks.addEventListener("change", () => {
    pushConfig({ max_clicks: parseOptionalInt(maxClicks) });
  });

  maxDuration.addEventListener("change", () => {
    pushConfig({ max_duration_ms: parseOptionalInt(maxDuration) });
  });

  alwaysOnTop.addEventListener("change", () => {
    pushConfig({ always_on_top: alwaysOnTop.checked });
  });

  compactMode.addEventListener("change", () => {
    applyCompactMode(compactMode.checked);
    call("set_compact_mode", compactMode.checked);
  });

  fixedX.addEventListener("change", () => {
    const x = parseInt(fixedX.value || "0", 10) || 0;
    pushConfig({ fixed_x: x, position_mode: "fixed" });
  });

  fixedY.addEventListener("change", () => {
    const y = parseInt(fixedY.value || "0", 10) || 0;
    pushConfig({ fixed_y: y, position_mode: "fixed" });
  });

  wfEnabled.addEventListener("change", () => {
    pushWindowFilter({ enabled: wfEnabled.checked });
  });

  wfProcess.addEventListener("change", () => {
    pushWindowFilter({ process: (wfProcess.value || "").trim() });
  });

  wfTitle.addEventListener("change", () => {
    pushWindowFilter({ title_contains: (wfTitle.value || "").trim() });
  });

  burstCount.addEventListener("change", () => {
    pushConfig({ burst_count: parseOptionalInt(burstCount) });
  });

  burstPause.addEventListener("change", () => {
    pushConfig({ burst_pause_ms: parseOptionalNonNeg(burstPause) });
  });

  pickBtn.addEventListener("click", () => call("pick_location"));

  addSeqBtn.addEventListener("click", () => {
    const delay = Math.max(0, parseInt(seqDelay.value || "0", 10) || 0);
    // Usa XY do ponto fixo se modo fixed; senão cursor atual (omitido)
    if (localConfig.position_mode === "fixed") {
      call("add_sequence_point", localConfig.fixed_x, localConfig.fixed_y, delay);
    } else {
      call("add_sequence_point", null, null, delay);
    }
  });

  clearSeqBtn.addEventListener("click", () => call("clear_sequence"));

  hotkeyBtn.addEventListener("click", async () => {
    const recording = hotkeyBtn.classList.contains("recording");
    await call(recording ? "cancel_record_hotkey" : "record_hotkey");
  });

  saveProfileBtn.addEventListener("click", async () => {
    const name = (profileName.value || profileList.value || "").trim();
    if (!name) {
      showLocalError(t("profiles.needName"));
      return;
    }
    const state = await call("save_profile", name);
    if (state && state.saved_profile) profileName.value = state.saved_profile;
  });

  loadProfileBtn.addEventListener("click", async () => {
    const name = (profileList.value || profileName.value || "").trim();
    if (!name) {
      showLocalError(t("profiles.needSelect"));
      return;
    }
    const state = await call("load_profile", name);
    if (state && !state.last_error) profileName.value = name;
  });

  exportProfileBtn.addEventListener("click", () => {
    call("export_profile", (profileName.value || profileList.value || "").trim());
  });

  importProfileBtn.addEventListener("click", async () => {
    const state = await call("import_profile", (profileName.value || "").trim());
    if (state && state.imported_profile) profileName.value = state.imported_profile;
  });

  profileList.addEventListener("change", () => {
    if (profileList.value) profileName.value = profileList.value;
  });

  profileList.addEventListener("dblclick", () => {
    loadProfileBtn.click();
  });

  macroRecordBtn.addEventListener("click", async () => {
    const recording = macroRecordBtn.dataset.recording === "1";
    await call(recording ? "macro_record_stop" : "macro_record_start");
  });

  macroPlayBtn.addEventListener("click", () => call("macro_play"));
  macroStopBtn.addEventListener("click", () => call("macro_stop"));
  macroClearBtn.addEventListener("click", () => call("macro_clear"));

  scriptRunBtn.addEventListener("click", () => call("script_run", scriptSource.value || ""));
  scriptStopBtn.addEventListener("click", () => call("script_stop"));

  scheduleSetBtn.addEventListener("click", () => {
    call("schedule_set", (scheduleAt.value || "").trim());
  });
  scheduleCancelBtn.addEventListener("click", () => call("schedule_cancel"));

  mainBtn.addEventListener("click", () => {
    toggleRun();
  });

  const winMin = document.getElementById("winMin");
  const winClose = document.getElementById("winClose");
  if (winMin) {
    winMin.addEventListener("click", (e) => {
      e.stopPropagation();
      call("window_minimize");
    });
  }
  const trayModal = document.getElementById("trayModal");
  const trayModalOk = document.getElementById("trayModalOk");
  const trayModalCancel = document.getElementById("trayModalCancel");

  function openTrayModal() {
    if (!trayModal) return;
    trayModal.hidden = false;
    if (trayModalOk) trayModalOk.focus();
  }

  function closeTrayModal() {
    if (!trayModal) return;
    trayModal.hidden = true;
  }

  if (winClose) {
    winClose.addEventListener("click", (e) => {
      e.stopPropagation();
      openTrayModal();
    });
  }
  if (trayModalCancel) {
    trayModalCancel.addEventListener("click", () => {
      closeTrayModal();
    });
  }
  if (trayModalOk) {
    trayModalOk.addEventListener("click", () => {
      closeTrayModal();
      call("window_close");
    });
  }
  if (trayModal) {
    trayModal.addEventListener("click", (e) => {
      if (e.target === trayModal) closeTrayModal();
    });
  }

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      if (tab.hidden) return;
      activateTab(tab.dataset.tab);
    });
  });

  document.querySelectorAll(".segmented").forEach((group) => {
    group.addEventListener("click", (e) => {
      const btn = e.target.closest(".seg");
      if (!btn) return;
      group.querySelectorAll(".seg").forEach((s) => s.classList.remove("active"));
      btn.classList.add("active");
      const key = group.dataset.group;
      const val = btn.dataset.val;
      const payload = {};
      payload[key] = val;
      if (key === "click_type") {
        payload.hold = val === "hold";
      }
      pushConfig(payload);
    });
  });

  function hideSplash() {
    document.body.classList.remove("booting");
    const splash = document.getElementById("splash");
    if (splash) {
      splash.setAttribute("aria-busy", "false");
    }
  }

  function formatVersionLabel(version) {
    const raw = String(version || "").trim();
    if (!raw) return "";
    return raw.charAt(0).toLowerCase() === "v" ? raw : "v" + raw;
  }

  function applyVersion(version) {
    const label = formatVersionLabel(version);
    const splashEl = document.getElementById("splashVersion");
    const footerEl = document.getElementById("appVersion");
    if (splashEl) {
      if (label) {
        splashEl.textContent = label;
        splashEl.hidden = false;
      } else {
        splashEl.textContent = "";
        splashEl.hidden = true;
      }
    }
    if (footerEl) {
      if (label) {
        footerEl.textContent = label;
        footerEl.hidden = false;
      } else {
        footerEl.textContent = "";
        footerEl.hidden = true;
      }
    }
  }

  function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  function showLocaleGate() {
    const gate = document.getElementById("localeGate");
    const list = document.getElementById("localeGateList");
    if (!gate || !list || !window.ClickrI18n) {
      return Promise.resolve(null);
    }
    return new Promise((resolve) => {
      list.innerHTML = "";
      window.ClickrI18n.SUPPORTED.forEach((code) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "locale-gate-btn";
        btn.textContent = window.ClickrI18n.LABELS[code] || code;
        btn.addEventListener("click", () => resolve(code));
        list.appendChild(btn);
      });
      gate.hidden = false;
    }).then((code) => {
      gate.hidden = true;
      return code;
    });
  }

  async function applyLocale(code, persist) {
    if (!window.ClickrI18n || !code) return;
    await window.ClickrI18n.setLocale(code);
    if (persist) {
      const bridge = api();
      if (bridge && bridge.set_locale) {
        await bridge.set_locale(code);
      }
    }
    if (window.ClickrManual && window.ClickrManual.reloadLocale) {
      window.ClickrManual.reloadLocale();
    }
    // Textos montados por código precisam ser refeitos no novo idioma.
    lastSequenceKey = null;
    await refreshState();
  }

  function bindLocaleSelect() {
    const select = document.getElementById("localeSelect");
    if (!select || !window.ClickrI18n) return;
    window.ClickrI18n.fillLocaleSelect(select);
    select.addEventListener("change", async () => {
      const code = select.value;
      try {
        await applyLocale(code, true);
      } catch (err) {
        showLocalError(String(err.message || err));
      }
    });
  }

  function bindManualHooks() {
    if (!window.ClickrManual) return;
    const requireOk = (state) => {
      if (!state) throw new Error(localError || t("errors.bridgeUnavailable"));
      if (state.last_error) throw new Error(formatError(state.last_error));
      return state;
    };
    window.ClickrManual.bind({
      activateTab,
      pushConfig,
      getConfig: () => ({ ...localConfig }),
      getState: async () => {
        const bridge = api();
        if (!bridge) return null;
        const state = await bridge.get_state();
        applyVisual(state);
        return state;
      },
      setError: (msg) => showLocalError(msg || ""),
      pickLocation: () => call("pick_location"),
      saveProfile: async (name) => {
        const state = requireOk(await call("save_profile", name));
        if (profileName) profileName.value = state.saved_profile || name;
        return state;
      },
      start: async () => requireOk(await call("start")),
    });
  }

  async function boot() {
    const splashStarted = Date.now();
    const minSplash =
      (window.ClickrManual && window.ClickrManual.MIN_SPLASH_MS) || 1100;
    try {
      await waitApi();
      if (window.ClickrI18n) {
        await window.ClickrI18n.loadLocale(window.ClickrI18n.FALLBACK);
      }
      bindLocaleSelect();

      const bridge = api();
      const settings = bridge && bridge.get_settings ? await bridge.get_settings() : {};
      if (settings && settings.version) {
        applyVersion(settings.version);
      }
      if (settings && Array.isArray(settings.profiles)) {
        refreshProfileList(settings.profiles);
      }

      const elapsedSplash = Date.now() - splashStarted;
      if (elapsedSplash < minSplash) {
        await delay(minSplash - elapsedSplash);
      }
      hideSplash();

      let locale = settings && settings.locale ? settings.locale : null;
      if (!locale) {
        locale = await showLocaleGate();
        if (locale) {
          await applyLocale(locale, true);
        } else if (window.ClickrI18n) {
          await applyLocale(window.ClickrI18n.FALLBACK, false);
        }
      } else {
        await applyLocale(locale, false);
      }

      await refreshState();
      startPolling();
      bindManualHooks();
      if (window.ClickrManual) {
        await window.ClickrManual.load();
        if (window.ClickrManual.shouldOpenOnFirstRun()) {
          window.ClickrManual.openFirstRun();
        }
      }
    } catch (err) {
      showLocalError(String(err.message || err));
      hideSplash();
    }
  }

  if (window.pywebview) {
    boot();
  } else {
    window.addEventListener("pywebviewready", boot);
    setTimeout(() => {
      if (!apiReady) {
        showLocalError(t("errors.waitingBridge"));
      }
    }, 800);
  }
})();
