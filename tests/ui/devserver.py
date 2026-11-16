"""
Servidor de desenvolvimento: serve ui/ e expõe o AppController REAL por HTTP.

A página recebe um `window.pywebview.api` que encaminha cada chamada para
POST /__api/<método>. Input usa o backend nulo e pywebview/pynput são dublês,
então roda em qualquer máquina (sem display). Usado pelos testes de UI.

Uso: python tests/ui/devserver.py [porta]   (dados em diretório temporário)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

os.environ["CLICKR_INPUT_BACKEND"] = "null"
_DATA = os.environ.get("CLICKR_TEST_DATA") or tempfile.mkdtemp(prefix="clickr-ui-")
os.environ["APPDATA"] = _DATA
os.environ["XDG_CONFIG_HOME"] = _DATA
os.environ["HOME"] = _DATA

import fakes  # noqa: E402

fakes.install_fake_webview()
fakes.install_fake_pynput()

from app.bootstrap import create_app  # noqa: E402

SHIM = """<script>
(function () {
  const api = new Proxy({}, {
    get(_t, name) {
      if (name === "then") return undefined;
      return async (...args) => {
        const res = await fetch("/__api/" + String(name), {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(args),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "bridge error");
        return data.result;
      };
    },
    has() { return true; },
  });
  window.pywebview = { api };
  setTimeout(() => window.dispatchEvent(new Event("pywebviewready")), 0);
})();
</script>"""

TYPES = {".html": "text/html", ".js": "text/javascript", ".css": "text/css",
         ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png"}


def make_handler(controller, window):
    ui = ROOT / "ui"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silencioso
            pass

        def _send(self, code, body, ctype):
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            rel = self.path.split("?", 1)[0].lstrip("/") or "index.html"
            path = (ui / rel).resolve()
            if ui not in path.parents or not path.is_file():
                self._send(404, b"not found", "text/plain")
                return
            body = path.read_bytes()
            if path.suffix == ".html":
                body = body.replace(b"<head>", b"<head>" + SHIM.encode(), 1)
            self._send(200, body, TYPES.get(path.suffix, "application/octet-stream"))

        def do_POST(self):
            name = self.path.split("/__api/", 1)[-1]
            length = int(self.headers.get("Content-Length") or 0)
            try:
                args = json.loads(self.rfile.read(length) or b"[]")
                if name == "__test":
                    result = test_hook(controller, window, *args)
                elif name.startswith("_") or not callable(getattr(controller, name, None)):
                    raise AttributeError(f"método desconhecido: {name}")
                else:
                    result = getattr(controller, name)(*args)
                body = json.dumps({"result": result}, default=str).encode()
                self._send(200, body, "application/json")
            except Exception as exc:  # noqa: BLE001
                body = json.dumps({"error": f"{type(exc).__name__}: {exc}"}).encode()
                self._send(500, body, "application/json")

    return Handler


def test_hook(controller, window, action, *args):
    """Ações só de teste: inspecionar o input nulo, definir o diálogo de arquivo etc."""
    from core import sendinput_null

    if action == "input":
        return [list(c) for c in sendinput_null.recorded()]
    if action == "reset_input":
        sendinput_null.reset()
        return True
    if action == "dialog":
        window.dialog_result = args[0]
        return True
    if action == "data_dir":
        return _DATA
    if action == "cursor":
        sendinput_null.set_cursor_pos_for_test(int(args[0]), int(args[1]))
        return True
    raise ValueError(action)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    window, controller = create_app()
    controller.bootstrap_services()
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(controller, window))
    print(f"READY http://127.0.0.1:{port}/index.html data={_DATA}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        controller.shutdown()


if __name__ == "__main__":
    main()
