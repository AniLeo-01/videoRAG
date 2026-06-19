"""Minimal web frontend for the video RAG pipeline.

Run with:  python app.py   (then open http://localhost:8000)
Uses only the standard library so it adds no dependencies.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from src.pipeline import run_pipeline

PORT = 8000

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Video RAG</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: system-ui, -apple-system, sans-serif;
    background: #0e0f13; color: #e8e8ea; min-height: 100vh;
    display: flex; justify-content: center;
  }
  main { width: 100%; max-width: 720px; padding: 48px 20px 80px; }
  h1 { font-size: 22px; font-weight: 600; margin: 0 0 4px; }
  p.sub { margin: 0 0 28px; color: #8b8d96; font-size: 14px; }
  form { display: flex; gap: 8px; }
  input {
    flex: 1; padding: 12px 14px; border-radius: 10px; font-size: 15px;
    border: 1px solid #2a2c34; background: #16171d; color: #e8e8ea;
  }
  input:focus { outline: none; border-color: #4f7cff; }
  button {
    padding: 12px 18px; border: none; border-radius: 10px; font-size: 15px;
    background: #4f7cff; color: #fff; cursor: pointer; font-weight: 500;
  }
  button:disabled { opacity: .5; cursor: default; }
  #status { margin: 22px 0 0; color: #8b8d96; font-size: 14px; min-height: 18px; }
  #results { margin-top: 18px; display: grid; gap: 12px; }
  a.card {
    display: flex; gap: 14px; align-items: center; text-decoration: none;
    background: #16171d; border: 1px solid #2a2c34; border-radius: 12px;
    padding: 10px; color: inherit; transition: border-color .15s;
  }
  a.card:hover { border-color: #4f7cff; }
  a.card img { width: 160px; aspect-ratio: 16/9; object-fit: cover; border-radius: 8px; background: #000; }
  a.card span { font-size: 14px; word-break: break-all; color: #9fb4ff; }
</style>
</head>
<body>
<main>
  <h1>Video RAG</h1>
  <p class="sub">Search game trailers by describing what you want to see.</p>
  <form id="form">
    <input id="q" placeholder="e.g. horror action with guns and monsters" autocomplete="off" autofocus>
    <button id="go" type="submit">Search</button>
  </form>
  <p id="status"></p>
  <div id="results"></div>
</main>
<script>
  const form = document.getElementById('form');
  const input = document.getElementById('q');
  const go = document.getElementById('go');
  const status = document.getElementById('status');
  const results = document.getElementById('results');

  function thumb(url) {
    const m = url.match(/[?&]v=([^&]+)/);
    return m ? `https://img.youtube.com/vi/${m[1]}/mqdefault.jpg` : '';
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;
    go.disabled = true;
    results.innerHTML = '';
    status.textContent = 'Searching…';
    try {
      const res = await fetch('/api/search?q=' + encodeURIComponent(query));
      const data = await res.json();
      const links = data.links || [];
      if (!links.length) {
        status.textContent = 'No relevant videos found.';
      } else {
        status.textContent = `${links.length} result${links.length > 1 ? 's' : ''}`;
        results.innerHTML = links.map(url =>
          `<a class="card" href="${url}" target="_blank" rel="noopener">
             <img src="${thumb(url)}" alt="">
             <span>${url}</span>
           </a>`).join('');
      }
    } catch (err) {
      status.textContent = 'Error: ' + err.message;
    } finally {
      go.disabled = false;
    }
  });
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif parsed.path == "/api/search":
            query = (parse_qs(parsed.query).get("q") or [""])[0].strip()
            try:
                links = run_pipeline(query) if query else []
                self._send(200, json.dumps({"links": links}), "application/json")
            except Exception as exc:
                self._send(500, json.dumps({"error": str(exc)}), "application/json")
        else:
            self._send(404, json.dumps({"error": "not found"}), "application/json")

    def log_message(self, *args):
        pass  # quiet default request logging


if __name__ == "__main__":
    print(f"Video RAG running at http://localhost:{PORT}")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
