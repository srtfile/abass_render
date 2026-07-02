import requests
import re
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Origin": "https://playhydrax.com",
    "Referer": "https://playhydrax.com/"
}

API = "https://enc-dec.app/api"

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Abyss Extractor</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0e0; min-height: 100vh; padding: 20px; }
  .container { max-width: 900px; margin: 0 auto; }
  h1 { text-align: center; color: #00bcd4; margin-bottom: 8px; font-size: 2rem; }
  .subtitle { text-align: center; color: #888; margin-bottom: 30px; font-size: 0.9rem; }
  .card { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
  label { display: block; margin-bottom: 6px; color: #aaa; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; }
  input { width: 100%; padding: 10px 14px; background: #0f0f1a; border: 1px solid #3a3a5a; border-radius: 8px; color: #e0e0e0; font-size: 0.95rem; margin-bottom: 16px; outline: none; }
  input:focus { border-color: #00bcd4; }
  button { width: 100%; padding: 12px; background: #00bcd4; color: #000; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
  button:hover { background: #00a0b8; }
  button:disabled { background: #444; color: #888; cursor: not-allowed; }
  .output { background: #0a0a15; border: 1px solid #2a2a4a; border-radius: 8px; padding: 16px; min-height: 120px; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; word-break: break-all; color: #a0f0a0; }
  .step { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #2a2a4a; color: #888; font-size: 0.85rem; }
  .step:last-child { border-bottom: none; }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: #444; flex-shrink: 0; }
  .step.done .dot { background: #4caf50; }
  .step.active .dot { background: #00bcd4; animation: pulse 1s infinite; }
  .step.error .dot { background: #f44336; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; background: #2a2a4a; color: #00bcd4; margin-left: 8px; }
  .error-msg { color: #f44336; }
</style>
</head>
<body>
<div class="container">
  <h1>🌊 Abyss</h1>
  <p class="subtitle">Extract decrypted stream data from playhydrax.com</p>
  <div class="card">
    <label>Content ID</label>
    <input type="text" id="content_id" value="K8R6OOjS7" placeholder="e.g. K8R6OOjS7">
    <button id="runBtn" onclick="run()">▶ Extract Stream Data</button>
  </div>
  <div class="card">
    <label>Progress</label>
    <div id="steps">
      <div class="step" id="s1"><div class="dot"></div> Fetch Encrypted Data</div>
      <div class="step" id="s2"><div class="dot"></div> Decrypt Stream Data</div>
    </div>
  </div>
  <div class="card">
    <label>Output <span class="badge" id="badge"></span></label>
    <div class="output" id="output">Results will appear here...</div>
  </div>
</div>
<script>
async function run() {
  const btn = document.getElementById('runBtn');
  btn.disabled = true;
  document.getElementById('output').textContent = 'Running...';
  document.getElementById('badge').textContent = '';
  ['s1','s2'].forEach(id => document.getElementById(id).className = 'step');

  try {
    const resp = await fetch('/run', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ content_id: document.getElementById('content_id').value })
    });
    const data = await resp.json();
    data.steps.forEach((s, i) => {
      document.getElementById('s'+(i+1)).classList.add(s.status);
    });
    if (data.error) {
      document.getElementById('output').innerHTML = '<span class="error-msg">ERROR: ' + data.error + '</span>';
      document.getElementById('badge').textContent = 'FAILED';
    } else {
      document.getElementById('output').textContent = JSON.stringify(data.result, null, 2);
      document.getElementById('badge').textContent = 'SUCCESS';
    }
  } catch(e) {
    document.getElementById('output').innerHTML = '<span class="error-msg">' + e.message + '</span>';
  }
  btn.disabled = false;
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/run', methods=['POST'])
def run():
    content_id = request.json.get('content_id', '')
    steps = [
        {"label": "Fetch Encrypted Data", "status": "active"},
        {"label": "Decrypt Stream Data", "status": ""},
    ]
    try:
        url = f"https://playhydrax.com/?v={content_id}"
        response = requests.get(url, headers=HEADERS, timeout=15).text
        match = re.search(r'const\s+datas\s*=\s*"([^"]*)"', response)
        if not match:
            steps[0]["status"] = "error"
            return jsonify({"steps": steps, "error": "Could not find encrypted data on page"})
        encrypted = match.group(1)
        steps[0]["status"] = "done"

        steps[1]["status"] = "active"
        dec_resp = requests.post(f"{API}/dec-abyss", json={"text": encrypted}, timeout=10).json()
        if dec_resp.get("status") != 200:
            steps[1]["status"] = "error"
            return jsonify({"steps": steps, "error": dec_resp.get("error", "Decryption failed")})
        decrypted = dec_resp["result"]
        steps[1]["status"] = "done"

        return jsonify({"steps": steps, "result": decrypted})
    except Exception as e:
        for s in steps:
            if s["status"] == "active":
                s["status"] = "error"
        return jsonify({"steps": steps, "error": str(e)})

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
