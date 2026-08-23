from flask import Flask, request, jsonify
from urllib.parse import urlparse, parse_qs
import requests

app = Flask(__name__)

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
            
            return jsonify({
                "status": "success",
                    "access_token": q.get("access_token", ["N/A"])[0],
                    "name": q.get("nickname", ["N/A"])[0],
                    "uid": q.get("account_id", ["N/A"])[0],
                    "region": q.get("region", ["N/A"])[0],
                	"credits": "@RFG_GAMER"
            }), 200
        else:
            return jsonify({"status": "error", "message": "Invalid Token or expired link"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Local Server Run Settings (Port: 5283)
    app.run(host="0.0.0.0", port=5283, debug=True)
