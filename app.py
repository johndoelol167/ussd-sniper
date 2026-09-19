from flask import Flask, render_template_string, request, jsonify
import requests
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Modern Dark-Themed UI Dashboard Template
HTML_DASHBOARD = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Advanced USSD Sniper - Discord (Turbo)</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121214; color: #e1e1e6; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #1a1a1e; padding: 30px; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); width: 420px; border: 1px solid #2d2d35; }
        h2 { text-align: center; color: #5865F2; margin-bottom: 5px; }
        p.subtitle { text-align: center; color: #8f8f9d; font-size: 13px; margin-top: 0; margin-bottom: 25px; }
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
        .stat-box { background: #222228; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #2f2f38; }
        .stat-box span { display: block; font-size: 18px; font-weight: bold; margin-top: 5px; }
        .stat-box.available span { color: #3ba55d; }
        .stat-box.taken span { color: #ed4245; }
        textarea { width: 100%; height: 100px; padding: 10px; border-radius: 6px; border: 1px solid #2f2f38; background: #121214; color: white; font-size: 14px; resize: none; box-sizing: border-box; margin-bottom: 15px; }
        button { width: 100%; background: #5865F2; color: white; border: none; padding: 12px; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #4752C4; }
        .console { background: #121214; border: 1px solid #2f2f38; border-radius: 6px; padding: 10px; height: 120px; overflow-y: auto; font-family: monospace; font-size: 12px; margin-top: 15px; color: #a1a1b0; }
        .log-success { color: #3ba55d; }
        .log-taken { color: #ed4245; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Advanced USSD Sniper</h2>
        <p class="subtitle">Discord Turbo Edition</p>
        
        <div class="stats-grid">
            <div class="stat-box available">
                Available Found
                <span id="avail-count">0</span>
            </div>
            <div class="stat-box taken">
                Checked Total
                <span id="checked-count">0</span>
            </div>
        </div>

        <form id="sniper-form">
            <label style="font-size: 13px; color: #8f8f9d;">Usernames (one per line):</label>
            <textarea id="usernames-input" placeholder="cool&#10;test&#10;name"></textarea>
            <button type="button" onclick="startTurboSniper()">Start Turbo Sniper</button>
        </form>

        <div class="console" id="console-box">
            [System] Turbo Sniper initialized...<br>
        </div>
    </div>

    <script>
        async function startTurboSniper() {
            const rawText = document.getElementById('usernames-input').value;
            const usernames = rawText.split('\\n').map(u => u.trim()).filter(u => u.length > 0);
            
            if (usernames.length === 0) {
                alert("Please enter at least one username!");
                return;
            }

            const consoleBox = document.getElementById('console-box');
            consoleBox.innerHTML += `[System] Dispatching batch of ${usernames.length} username(s) concurrently...<br>`;
            consoleBox.scrollTop = consoleBox.scrollHeight;

            try {
                let response = await fetch('/check-batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ usernames: usernames })
                });
                
                let data = await response.json();
                let results = data.results;

                let availCount = parseInt(document.getElementById('avail-count').innerText);
                let checkedCount = parseInt(document.getElementById('checked-count').innerText);

                results.forEach(res => {
                    checkedCount++;
                    if (res.status === 'available') {
                        availCount++;
                        consoleBox.innerHTML += `<span class="log-success">[+] AVAILABLE: ${res.username}</span><br>`;
                    } else if (res.status === 'taken') {
                        consoleBox.innerHTML += `<span class="log-taken">[-] Taken: ${res.username}</span><br>`;
                    } else {
                        consoleBox.innerHTML += `[!] Rate-limited / Error on: ${res.username}<br>`;
                    }
                });

                document.getElementById('avail-count').innerText = availCount;
                document.getElementById('checked-count').innerText = checkedCount;
                consoleBox.innerHTML += `[System] Batch scan complete!<br>`;
                consoleBox.scrollTop = consoleBox.scrollHeight;

            } catch (err) {
                consoleBox.innerHTML += `[!] Network exception during batch request<br>`;
            }
        }
    </script>
</body>
</html>
"""

# Configure your token here
DISCORD_TOKEN = "MTU0OTIyMzE0NTM4OTQyODc0Ng.GsUN_K._zBNwDT-4W0FmYWp7eammtbmTZ9GC4-z3yfRJI"

def check_single_username(username):
    target_url = "https://discord.com/api/v9/users/@me/pomelo-attempt"
    headers = {
        "Authorization": DISCORD_TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {"username": username}
    
    try:
        response = requests.post(target_url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("taken") is False:
                return {"username": username, "status": "available"}
            else:
                return {"username": username, "status": "taken"}
        else:
            return {"username": username, "status": "limited"}
    except Exception:
        return {"username": username, "status": "error"}

@app.route("/")
def index():
    return render_template_string(HTML_DASHBOARD)

@app.route("/check-batch", methods=["POST"])
def check_batch():
    data = request.get_json()
    usernames = data.get("usernames", [])
    
    if not usernames:
        return jsonify({"results": []})

    # Use ThreadPoolExecutor to check multiple usernames simultaneously (e.g., 5 at a time)
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(check_single_username, usernames))
        
    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
