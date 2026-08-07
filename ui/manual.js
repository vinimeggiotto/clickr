(() => {
  const STORAGE_GUIDE = "clickr_manual_seen_v1";
  const STORAGE_WIZARD = "clickr_wizard_done_v1";
  const MIN_SPLASH_MS = 1100;

  const GUIDE_ORDER = [
    { id: "welcome", goto: null },
    { id: "click", goto: "click" },
    { id: "run", goto: "run" },
    { id: "point", goto: "point" },
    { id: "profiles", goto: "profiles" },
    { id: "advanced", goto: "advanced" },
    { id: "macro", goto: "macro" },
    { id: "script", goto: "script" },
    { id: "schedule", goto: "schedule" },
    { id: "safety", goto: null },
  ];

  const WIZARD_STEPS = [
    "welcome",
    "button",
    "click_type",
    "interval",
    "position",
    "limits",
    "profile",
    "finish",
  ];

  const INFO_KEYS = [
    "mouse_buttons",
    "click_type",
    "interval",
    "position",
    "limits",
    "delay",
    "jitter",
    "max_clicks",
    "max_duration",
    "profile",
  ];

  const api = {
    activateTab: null,
    pushConfig: null,
    pickLocation: null,
    saveProfile: null,
    start: null,
    getConfig: null,
    getState: null,
    setError: null,
  };

  const manualGuide = document.getElementById("manualGuide");
  const manualWizard = document.getElementById("manualWizard");
  const modeGuide = document.getElementById("modeGuide");
  const modeWizard = document.getElementById("modeWizard");
  const manualBody = document.getElementById("manualBody");
  const manualStepLabel = document.getElementById("manualStepLabel");
  const manualPrev = document.getElementById("manualPrev");
  const manualNext = document.getElementById("manualNext");
  const manualTry = document.getElementById("manualTry");

  let guideSteps = [];
  let guideIndex = 0;

  const wizBody = document.getElementById("wizBody");
  const wizStepLabel = document.getElementById("wizStepLabel");
  const wizPrev = document.getElementById("wizPrev");
  const wizNext = document.getElementById("wizNext");
  const wizHint = document.getElementById("wizHint");
  const wizActions = document.getElementById("wizActions");

  let wizIndex = 0;
  const draft = {
    button: "left",
    click_type: "single",
    hold: false,
    interval_ms: 80,
    position_mode: "cursor",
    fixed_x: 0,
    fixed_y: 0,
    start_delay_ms: 0,
    jitter_ms: 0,
    max_clicks: null,
    max_duration_ms: null,
    profile_name: "meu-primeiro-preset",
  };

  function t(key, vars) {
    return window.ClickrI18n ? window.ClickrI18n.t(key, vars) : key;
  }

  function tList(key) {
    return window.ClickrI18n ? window.ClickrI18n.tList(key) : [];
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function buildGuideSteps() {
    return GUIDE_ORDER.map((meta) => ({
      id: meta.id,
      goto: meta.goto,
      title: t(`manual.guide.${meta.id}.title`),
      body: tList(`manual.guide.${meta.id}.body`),
      tips: tList(`manual.guide.${meta.id}.tips`),
    }));
  }

  function setMode(mode) {
    const wizard = mode === "wizard";
    if (modeGuide) modeGuide.classList.toggle("active", !wizard);
    if (modeWizard) modeWizard.classList.toggle("active", wizard);
    if (manualGuide) manualGuide.hidden = wizard;
    if (manualWizard) manualWizard.hidden = !wizard;
    if (wizard) renderWizard();
  }

  function renderGuide() {
    if (!manualBody || !guideSteps.length) return;
    const step = guideSteps[guideIndex];
    const parts = [];
    parts.push(`<h3 class="manual-title">${escapeHtml(step.title)}</h3>`);
    (step.body || []).forEach((p) => {
      parts.push(`<p class="manual-p">${escapeHtml(p)}</p>`);
    });
    if (step.tips && step.tips.length) {
      parts.push('<ul class="manual-tips">');
      step.tips.forEach((tip) => parts.push(`<li>${escapeHtml(tip)}</li>`));
      parts.push("</ul>");
    }
    manualBody.innerHTML = parts.join("");
    if (manualStepLabel) {
      manualStepLabel.textContent = `${guideIndex + 1} / ${guideSteps.length}`;
    }
    if (manualPrev) manualPrev.disabled = guideIndex <= 0;
    if (manualNext) {
      manualNext.textContent =
        guideIndex >= guideSteps.length - 1
          ? t("manualUi.finish")
          : t("manualUi.next");
    }
    if (manualTry) {
      const hasGoto = !!(step.goto && api.activateTab);
      manualTry.hidden = !hasGoto;
      if (hasGoto) {
        const tabLabel = t(`manual.goto.${step.goto}`);
        manualTry.textContent = t("manualUi.tryTab", { tab: tabLabel });
      }
    }
  }

  function guideGo(delta) {
    const next = guideIndex + delta;
    if (next < 0) return;
    if (next >= guideSteps.length) {
      try {
        localStorage.setItem(STORAGE_GUIDE, "1");
      } catch (_) {
        /* ignore */
      }
      if (api.activateTab) api.activateTab("click");
      return;
    }
    guideIndex = next;
    renderGuide();
  }

  async function loadManual() {
    draft.profile_name = t("manual.wizard.defaultProfile");
    guideSteps = buildGuideSteps();
    guideIndex = 0;
    renderGuide();
    syncDraftFromConfig();
    renderWizard();
  }

  function reloadLocale() {
    const keepGuide = guideIndex;
    const keepWiz = wizIndex;
    draft.profile_name = t("manual.wizard.defaultProfile");
    guideSteps = buildGuideSteps();
    guideIndex = Math.min(keepGuide, Math.max(0, guideSteps.length - 1));
    wizIndex = Math.min(keepWiz, Math.max(0, WIZARD_STEPS.length - 1));
    renderGuide();
    renderWizard();
  }

  function syncDraftFromConfig() {
    const cfg = api.getConfig ? api.getConfig() : null;
    if (!cfg) return;
    draft.button = cfg.button || draft.button;
    draft.click_type = cfg.hold ? "hold" : cfg.click_type || draft.click_type;
    draft.hold = !!cfg.hold;
    draft.interval_ms = cfg.interval_ms || draft.interval_ms;
    draft.position_mode = cfg.position_mode || draft.position_mode;
    draft.fixed_x = cfg.fixed_x || 0;
    draft.fixed_y = cfg.fixed_y || 0;
    draft.start_delay_ms = cfg.start_delay_ms || 0;
    draft.jitter_ms = cfg.jitter_ms || 0;
    draft.max_clicks = cfg.max_clicks;
    draft.max_duration_ms = cfg.max_duration_ms;
  }

  function wizCps() {
    const ms = Math.max(1, draft.interval_ms | 0);
    return (1000 / ms).toFixed(1);
  }

  function infoPayload(key) {
    if (!INFO_KEYS.includes(key)) return null;
    return {
      title: t(`manual.info.${key}.title`),
      body: tList(`manual.info.${key}.body`),
    };
  }

  function infoBtn(key) {
    const label = escapeHtml(t("manualUi.moreInfo"));
    return `<button type="button" class="info-btn" data-info="${key}" aria-label="${label}" title="${label}">i</button>`;
  }

  function titleWithInfo(title, key) {
    return `<h3 class="manual-title"><span>${escapeHtml(title)}</span> ${infoBtn(key)}</h3>`;
  }

  function labelWithInfo(forId, text, key) {
    return `<label for="${forId}" class="label-with-info"><span>${escapeHtml(text)}</span> ${infoBtn(key)}</label>`;
  }

  function segHtml(group, options, current) {
    const buttons = options
      .map(([val, label]) => {
        const active = val === current ? " active" : "";
        return `<button type="button" class="seg${active}" data-wiz-set="${group}" data-val="${val}">${label}</button>`;
      })
      .join("");
    return `<div class="segmented dense wiz-seg" role="group">${buttons}</div>`;
  }

  async function openInfoWindow(key) {
    const data = infoPayload(key);
    if (!data) return;
    const bridge = window.pywebview && window.pywebview.api;
    if (!bridge || !bridge.show_info_popup) {
      if (api.setError) api.setError(t("errors.infoUnavailable"));
      return;
    }
    const bodyHtml = (data.body || []).map((p) => `<p>${p}</p>`).join("");
    try {
      await bridge.show_info_popup(data.title, bodyHtml);
    } catch (err) {
      if (api.setError) api.setError(String(err.message || err));
    }
  }

  function renderWizard() {
    if (!wizBody) return;
    const id = WIZARD_STEPS[wizIndex];
    let html = "";
    let nextLabel = t("manualUi.next");
    let showActions = true;
    let hint = t("manual.wizard.hintInfo");

    if (id === "welcome") {
      html = `
        ${titleWithInfo(t("manual.wizard.welcomeTitle"), "profile")}
        <p class="manual-p">${escapeHtml(t("manual.wizard.welcomeBody"))}</p>
        <p class="manual-p dim-inline">${escapeHtml(t("manual.wizard.welcomeNote"))}</p>`;
    } else if (id === "button") {
      html = `
        ${titleWithInfo(t("manual.wizard.buttonTitle"), "mouse_buttons")}
        <p class="manual-p">${escapeHtml(t("manual.wizard.buttonBody"))}</p>
        ${segHtml(
          "button",
          [
            ["left", "L"],
            ["right", "R"],
            ["middle", "M"],
            ["x1", "4"],
            ["x2", "5"],
          ],
          draft.button
        )}
        <p class="manual-p dim-inline">${escapeHtml(t("manual.wizard.buttonNote"))}</p>`;
    } else if (id === "click_type") {
      html = `
        ${titleWithInfo(t("manual.wizard.typeTitle"), "click_type")}
        <p class="manual-p">${escapeHtml(t("manual.wizard.typeBody"))}</p>
        ${segHtml(
          "click_type",
          [
            ["single", t("click.single")],
            ["double", t("click.double")],
            ["hold", t("click.hold")],
          ],
          draft.click_type
        )}`;
    } else if (id === "interval") {
      html = `
        ${titleWithInfo(t("manual.wizard.intervalTitle"), "interval")}
        <p class="manual-p">${escapeHtml(t("manual.wizard.intervalBody"))}</p>
        <div class="lcd-input">
          <input type="number" id="wizInterval" value="${draft.interval_ms}" min="1" max="2000">
          <span>ms</span>
        </div>
        <input type="range" class="fader" id="wizIntervalSlider" min="10" max="500" value="${Math.min(500, Math.max(10, draft.interval_ms))}">
        <div class="cps">≈ <span id="wizCps">${wizCps()}</span> ${escapeHtml(t("brand.cpsSuffix"))}</div>`;
    } else if (id === "position") {
      const posHint =
        draft.position_mode === "fixed"
          ? t("point.fixedPoint", { x: draft.fixed_x, y: draft.fixed_y })
          : escapeHtml(t("manual.wizard.positionCursorHint"));
      html = `
        ${titleWithInfo(t("manual.wizard.positionTitle"), "position")}
        <p class="manual-p">${escapeHtml(t("manual.wizard.positionBody"))}</p>
        ${segHtml(
          "position_mode",
          [
            ["cursor", t("click.cursor")],
            ["fixed", t("click.fixed")],
          ],
          draft.position_mode
        )}
        <div class="fixed-hint" id="wizPosHint">${posHint}</div>
        <button type="button" class="action-btn" id="wizPick" ${
          draft.position_mode === "fixed" ? "" : "hidden"
        }>${escapeHtml(t("point.pick"))}</button>`;
    } else if (id === "limits") {
      html = `
        ${titleWithInfo(t("manual.wizard.limitsTitle"), "limits")}
        <p class="manual-p">${escapeHtml(t("manual.wizard.limitsBody"))}</p>
        <div class="field-grid">
          <div class="field">
            ${labelWithInfo("wizDelay", t("run.startDelay"), "delay")}
            <div class="lcd-input compact">
              <input type="number" id="wizDelay" value="${draft.start_delay_ms}" min="0" step="100">
              <span>ms</span>
            </div>
          </div>
          <div class="field">
            ${labelWithInfo("wizJitter", t("run.jitter"), "jitter")}
            <div class="lcd-input compact">
              <input type="number" id="wizJitter" value="${draft.jitter_ms}" min="0">
              <span>ms</span>
            </div>
          </div>
          <div class="field">
            ${labelWithInfo("wizMaxClicks", t("run.maxClicks"), "max_clicks")}
            <div class="lcd-input compact">
              <input type="number" id="wizMaxClicks" value="${draft.max_clicks == null ? "" : draft.max_clicks}" min="1" placeholder="∞">
              <span>n</span>
            </div>
          </div>
          <div class="field">
            ${labelWithInfo("wizMaxDur", t("run.maxDuration"), "max_duration")}
            <div class="lcd-input compact">
              <input type="number" id="wizMaxDur" value="${draft.max_duration_ms == null ? "" : draft.max_duration_ms}" min="1" placeholder="∞">
              <span>ms</span>
            </div>
          </div>
        </div>`;
      nextLabel = t("manualUi.continue");
    } else if (id === "profile") {
      html = `
        ${titleWithInfo(t("manual.wizard.profileTitle"), "profile")}
        <p class="manual-p">${escapeHtml(t("manual.wizard.profileBody"))}</p>
        <div class="lcd-input">
          <input type="text" id="wizProfileName" maxlength="64" value="${escapeHtml(draft.profile_name)}" autocomplete="off">
        </div>
        <p class="manual-p dim-inline">${escapeHtml(t("manual.wizard.profileNote"))}</p>`;
    } else if (id === "finish") {
      showActions = false;
      hint = "";
      const summaryPos =
        draft.position_mode === "fixed"
          ? t("manual.wizard.finishSummaryFixed", {
              x: draft.fixed_x,
              y: draft.fixed_y,
            })
          : t("manual.wizard.finishSummaryCursor");
      html = `
        <h3 class="manual-title">${escapeHtml(t("manual.wizard.finishTitle"))}</h3>
        <p class="manual-p">${t("manual.wizard.finishProfile", {
          name: escapeHtml(draft.profile_name),
        })}</p>
        <p class="manual-p">${escapeHtml(
          `${draft.button.toUpperCase()} · ${draft.click_type} · ${draft.interval_ms} ms · ${summaryPos}`
        )}</p>
        <div class="action-row wiz-finish">
          <button type="button" class="action-btn ghost" id="wizSaveOnly">${escapeHtml(
            t("manual.wizard.saveOnly")
          )}</button>
          <button type="button" class="action-btn" id="wizSaveStart">${escapeHtml(
            t("manual.wizard.saveStart")
          )}</button>
        </div>
        <button type="button" class="action-btn ghost" id="wizBackEdit">${escapeHtml(
          t("manual.wizard.back")
        )}</button>
        <ul class="manual-tips">
          <li>${t("manual.wizard.finishTip1")}</li>
          <li>${t("manual.wizard.finishTip2")}</li>
          <li>${t("manual.wizard.finishTip3")}</li>
        </ul>`;
    }

    wizBody.innerHTML = html;
    if (wizStepLabel) {
      wizStepLabel.textContent = `${wizIndex + 1} / ${WIZARD_STEPS.length}`;
    }
    if (wizPrev) wizPrev.disabled = wizIndex <= 0 || id === "finish";
    if (wizNext) {
      wizNext.textContent = nextLabel;
      wizNext.hidden = !showActions;
    }
    if (wizActions) wizActions.hidden = !showActions;
    if (wizHint) wizHint.textContent = hint;

    bindWizardDom();
  }

  function parseOptInt(raw) {
    const text = String(raw || "").trim();
    if (text === "") return null;
    const n = parseInt(text, 10);
    if (!Number.isFinite(n) || n <= 0) return null;
    return n;
  }

  function bindWizardDom() {
    wizBody.querySelectorAll("[data-info]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        openInfoWindow(btn.getAttribute("data-info"));
      });
    });

    wizBody.querySelectorAll("[data-wiz-set]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const group = btn.getAttribute("data-wiz-set");
        const val = btn.getAttribute("data-val");
        if (group === "button") {
          draft.button = val;
          await applyDraftPartial({ button: val });
        } else if (group === "click_type") {
          draft.click_type = val;
          draft.hold = val === "hold";
          await applyDraftPartial({
            click_type: val,
            hold: draft.hold,
          });
        } else if (group === "position_mode") {
          draft.position_mode = val;
          await applyDraftPartial({ position_mode: val });
        }
        renderWizard();
      });
    });

    const interval = document.getElementById("wizInterval");
    const slider = document.getElementById("wizIntervalSlider");
    const cpsEl = document.getElementById("wizCps");
    const syncInterval = async (ms) => {
      draft.interval_ms = Math.max(1, parseInt(ms, 10) || 80);
      if (cpsEl) cpsEl.textContent = wizCps();
      if (interval) interval.value = String(draft.interval_ms);
      if (slider) slider.value = String(Math.min(500, Math.max(10, draft.interval_ms)));
      await applyDraftPartial({ interval_ms: draft.interval_ms });
    };
    if (interval) {
      interval.addEventListener("change", () => syncInterval(interval.value));
    }
    if (slider) {
      slider.addEventListener("input", () => syncInterval(slider.value));
    }

    const pick = document.getElementById("wizPick");
    if (pick && api.pickLocation) {
      pick.addEventListener("click", async () => {
        try {
          if (api.setError) api.setError(t("errors.pickHint"));
          await api.pickLocation();
          for (let i = 0; i < 150; i++) {
            await new Promise((r) => setTimeout(r, 200));
            const st = api.getState ? await api.getState() : null;
            if (st && !st.picking) {
              const cfg = st.config || {};
              draft.position_mode = "fixed";
              draft.fixed_x = cfg.fixed_x ?? draft.fixed_x;
              draft.fixed_y = cfg.fixed_y ?? draft.fixed_y;
              if (api.setError) api.setError("");
              renderWizard();
              return;
            }
          }
        } catch (err) {
          if (api.setError) api.setError(String(err.message || err));
        }
      });
    }

    const saveOnly = document.getElementById("wizSaveOnly");
    const saveStart = document.getElementById("wizSaveStart");
    const backEdit = document.getElementById("wizBackEdit");
    if (saveOnly) saveOnly.addEventListener("click", () => finishWizard(false));
    if (saveStart) saveStart.addEventListener("click", () => finishWizard(true));
    if (backEdit) {
      backEdit.addEventListener("click", () => {
        wizIndex = Math.max(0, WIZARD_STEPS.length - 2);
        renderWizard();
      });
    }
  }

  async function applyDraftPartial(partial) {
    if (api.pushConfig) await api.pushConfig(partial);
  }

  async function applyAllDraft() {
    await applyDraftPartial({
      button: draft.button,
      click_type: draft.click_type,
      hold: draft.hold || draft.click_type === "hold",
      interval_ms: draft.interval_ms,
      position_mode: draft.position_mode,
      fixed_x: draft.fixed_x,
      fixed_y: draft.fixed_y,
      start_delay_ms: draft.start_delay_ms,
      jitter_ms: draft.jitter_ms,
      max_clicks: draft.max_clicks,
      max_duration_ms: draft.max_duration_ms,
    });
  }

  async function readLimitsFromDom() {
    const delay = document.getElementById("wizDelay");
    const jitter = document.getElementById("wizJitter");
    const maxC = document.getElementById("wizMaxClicks");
    const maxD = document.getElementById("wizMaxDur");
    if (delay) draft.start_delay_ms = Math.max(0, parseInt(delay.value, 10) || 0);
    if (jitter) draft.jitter_ms = Math.max(0, parseInt(jitter.value, 10) || 0);
    if (maxC) draft.max_clicks = parseOptInt(maxC.value);
    if (maxD) draft.max_duration_ms = parseOptInt(maxD.value);
    await applyDraftPartial({
      start_delay_ms: draft.start_delay_ms,
      jitter_ms: draft.jitter_ms,
      max_clicks: draft.max_clicks,
      max_duration_ms: draft.max_duration_ms,
    });
  }

  async function wizGo(delta) {
    const id = WIZARD_STEPS[wizIndex];
    if (delta > 0) {
      if (id === "interval") {
        const el = document.getElementById("wizInterval");
        if (el) draft.interval_ms = Math.max(1, parseInt(el.value, 10) || 80);
        await applyDraftPartial({ interval_ms: draft.interval_ms });
      }
      if (id === "limits") await readLimitsFromDom();
      if (id === "profile") {
        const el = document.getElementById("wizProfileName");
        const name = (el && el.value ? el.value : draft.profile_name).trim();
        if (!name) {
          if (api.setError) api.setError(t("profiles.needName"));
          return;
        }
        draft.profile_name = name;
        if (api.setError) api.setError("");
      }
      if (id === "position" && draft.position_mode === "fixed") {
        await applyDraftPartial({
          position_mode: "fixed",
          fixed_x: draft.fixed_x,
          fixed_y: draft.fixed_y,
        });
      }
    }

    const next = wizIndex + delta;
    if (next < 0) return;
    if (next >= WIZARD_STEPS.length) return;
    wizIndex = next;
    renderWizard();
  }

  async function finishWizard(andStart) {
    try {
      await applyAllDraft();
      if (api.saveProfile) {
        await api.saveProfile(draft.profile_name);
      }
      try {
        localStorage.setItem(STORAGE_WIZARD, "1");
        localStorage.setItem(STORAGE_GUIDE, "1");
      } catch (_) {
        /* ignore */
      }
      if (andStart && api.start) {
        await api.start();
      }
      if (api.activateTab) api.activateTab("click");
      if (api.setError) {
        api.setError(
          andStart
            ? t("errors.wizardSavedStart", { name: draft.profile_name })
            : t("errors.wizardSavedOnly", { name: draft.profile_name })
        );
      }
    } catch (err) {
      if (api.setError) api.setError(String(err.message || err));
    }
  }

  function bind(hooks) {
    Object.assign(api, hooks || {});

    if (modeGuide) {
      modeGuide.addEventListener("click", () => setMode("guide"));
    }
    if (modeWizard) {
      modeWizard.addEventListener("click", () => setMode("wizard"));
    }
    if (manualPrev) manualPrev.addEventListener("click", () => guideGo(-1));
    if (manualNext) manualNext.addEventListener("click", () => guideGo(1));
    if (manualTry) {
      manualTry.addEventListener("click", () => {
        const step = guideSteps[guideIndex];
        if (step && step.goto && api.activateTab) api.activateTab(step.goto);
      });
    }
    if (wizPrev) wizPrev.addEventListener("click", () => wizGo(-1));
    if (wizNext) wizNext.addEventListener("click", () => wizGo(1));
  }

  function shouldOpenOnFirstRun() {
    try {
      return (
        localStorage.getItem(STORAGE_WIZARD) !== "1" &&
        localStorage.getItem(STORAGE_GUIDE) !== "1"
      );
    } catch (_) {
      return false;
    }
  }

  function openFirstRun() {
    setMode("wizard");
    wizIndex = 0;
    syncDraftFromConfig();
    renderWizard();
    if (api.activateTab) api.activateTab("manual");
  }

  window.ClickrManual = {
    load: loadManual,
    bind,
    shouldOpenOnFirstRun,
    openFirstRun,
    setMode,
    reloadLocale,
    MIN_SPLASH_MS,
  };
})();
