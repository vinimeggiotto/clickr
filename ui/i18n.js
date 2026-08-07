(() => {
  const SUPPORTED = ["pt-BR", "en-US", "zh-CN", "de-DE", "es-ES", "ru-RU"];
  const FALLBACK = "pt-BR";

  const LABELS = {
    "pt-BR": "Português (Brasil)",
    "en-US": "English (United States)",
    "zh-CN": "中文 (中国)",
    "de-DE": "Deutsch (Deutschland)",
    "es-ES": "Español (España)",
    "ru-RU": "Русский (Россия)",
  };

  let catalog = {};
  let fallbackCatalog = {};
  let current = FALLBACK;
  const listeners = [];

  function getByPath(obj, key) {
    if (!obj || !key) return undefined;
    const parts = String(key).split(".");
    let cur = obj;
    for (let i = 0; i < parts.length; i++) {
      if (cur == null || typeof cur !== "object") return undefined;
      cur = cur[parts[i]];
    }
    return cur;
  }

  function interpolate(str, vars) {
    if (!vars || typeof str !== "string") return str;
    return str.replace(/\{(\w+)\}/g, (_, name) =>
      vars[name] != null ? String(vars[name]) : `{${name}}`
    );
  }

  function resolve(key) {
    let val = getByPath(catalog, key);
    if (val === undefined) val = getByPath(fallbackCatalog, key);
    return val;
  }

  function t(key, vars) {
    const val = resolve(key);
    if (typeof val === "string") return interpolate(val, vars);
    if (val === undefined || val === null) return key;
    return val;
  }

  function tList(key) {
    const val = resolve(key);
    return Array.isArray(val) ? val.slice() : [];
  }

  function applyDom(root) {
    const scope = root || document;
    scope.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      const text = t(key);
      if (typeof text === "string") el.textContent = text;
    });
    scope.querySelectorAll("[data-i18n-html]").forEach((el) => {
      const key = el.getAttribute("data-i18n-html");
      const html = t(key);
      if (typeof html === "string") el.innerHTML = html;
    });
    scope.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      const text = t(key);
      if (typeof text === "string") el.setAttribute("placeholder", text);
    });
    scope.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const key = el.getAttribute("data-i18n-title");
      const text = t(key);
      if (typeof text === "string") el.setAttribute("title", text);
    });
    scope.querySelectorAll("[data-i18n-aria]").forEach((el) => {
      const key = el.getAttribute("data-i18n-aria");
      const text = t(key);
      if (typeof text === "string") el.setAttribute("aria-label", text);
    });
  }

  async function fetchCatalog(code) {
    const res = await fetch(`locales/${code}.json`, { cache: "no-store" });
    if (!res.ok) throw new Error(`Locale HTTP ${res.status}: ${code}`);
    return res.json();
  }

  async function loadLocale(code) {
    const safe = SUPPORTED.includes(code) ? code : FALLBACK;
    if (!Object.keys(fallbackCatalog).length || current === FALLBACK) {
      // always keep pt-BR fallback available
    }
    if (!Object.keys(fallbackCatalog).length) {
      fallbackCatalog = await fetchCatalog(FALLBACK);
    }
    if (safe === FALLBACK) {
      catalog = fallbackCatalog;
    } else {
      catalog = await fetchCatalog(safe);
    }
    current = safe;
    return current;
  }

  async function setLocale(code) {
    await loadLocale(code);
    document.documentElement.lang = current;
    applyDom(document);
    const select = document.getElementById("localeSelect");
    if (select && select.value !== current) select.value = current;
    listeners.forEach((fn) => {
      try {
        fn(current);
      } catch (_) {
        /* ignore */
      }
    });
    return current;
  }

  function onChange(fn) {
    if (typeof fn === "function") listeners.push(fn);
  }

  function getLocale() {
    return current;
  }

  function fillLocaleSelect(selectEl) {
    if (!selectEl) return;
    selectEl.innerHTML = "";
    SUPPORTED.forEach((code) => {
      const opt = document.createElement("option");
      opt.value = code;
      opt.textContent = LABELS[code] || code;
      selectEl.appendChild(opt);
    });
    selectEl.value = current;
  }

  window.ClickrI18n = {
    SUPPORTED,
    LABELS,
    FALLBACK,
    t,
    tList,
    applyDom,
    loadLocale,
    setLocale,
    getLocale,
    onChange,
    fillLocaleSelect,
  };
})();
