import os
import re
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PROVIDER_URL = "https://bantibhaiya.to/api/reseller_v1.php"
MASTER_KEY = "a7f3e8b2c9d1f4a6b8c2d5e9f1a3b6c8"
RESELLER_API_KEY = "f67105a05a812c45d3a5ffac39c58bd0"

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "online", "message": "SAHARAJ EXE Server Running"}), 200

@app.route("/api/buy", methods=["POST"])
def buy_key():
    try:
        data = request.get_json(force=True) or {}

        product_id = str(data.get("product_id") or "133").strip()
        raw_duration = str(data.get("duration") or "1 Hours").strip()
        option_id = str(data.get("option_id") or "1").strip()

        duration = re.sub(r'\[.*?\]', '', raw_duration).strip()

        headers = {
            "x-master-key": MASTER_KEY,
            "User-Agent": "Mozilla/5.0"
        }

        payload = {
            "api_key": RESELLER_API_KEY,
            "action": "buy",
            "product_id": product_id,
            "option_id": option_id,
            "duration": duration,
            "quantity": 1
        }

        res = requests.post(PROVIDER_URL, headers=headers, data=payload, timeout=25)

        try:
            res_data = res.json()
        except Exception:
            res_data = {"raw": res.text}

        key = None
        if isinstance(res_data, dict):
            key = (
                res_data.get("key") or 
                res_data.get("license_key") or 
                res_data.get("serial") or 
                res_data.get("code")
            )
            if not key and isinstance(res_data.get("data"), dict):
                key = res_data["data"].get("key") or res_data["data"].get("license_key")
            elif not key and isinstance(res_data.get("data"), list) and len(res_data["data"]) > 0:
                item = res_data["data"][0]
                key = item.get("key") if isinstance(item, dict) else item

        if key:
            return jsonify({
                "status": "success",
                "key": str(key).strip()
            }), 200

        err_msg = "Provider could not issue key"
        if isinstance(res_data, dict):
            err_msg = res_data.get("msg") or res_data.get("message") or res_data.get("error") or str(res_data)

        return jsonify({
            "status": "error",
            "message": err_msg
        }), 400

    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "message": "Provider timeout. Retry later."}), 504
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
