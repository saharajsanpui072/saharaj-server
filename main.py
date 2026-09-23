import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Provider API Credentials
PROVIDER_URL = "https://bantibhaiya.to/api/reseller_v1.php"
MASTER_KEY = "a7f3e8b2c9d1f4a6b8c2d5e9f1a3b6c8"
RESELLER_API_KEY = "f67105a05a812c45d3a5ffac39c58bd0"
DEFAULT_PRODUCT_ID = "133"

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "service": "SAHARAJ EXE Multi-Gadget Backend Proxy",
        "status": "online",
        "uptime": "24/7 Active"
    }), 200

@app.route("/api/buy", methods=["POST"])
def buy_key():
    try:
        req_data = request.get_json() or {}
        
        # Dynamic Product ID from admin/client
        product_id = str(req_data.get("product_id") or DEFAULT_PRODUCT_ID).strip()
        
        # Dynamic Duration / Provider option name set in Admin panel
        duration = str(req_data.get("duration") or "1 Hours").strip()
        
        # Dynamic Option ID
        option_id = str(req_data.get("option_id") or "1").strip()

        headers = {
            "x-master-key": MASTER_KEY,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

        # Form-encoded payload as required by standard reseller endpoints
        payload = {
            "api_key": RESELLER_API_KEY,
            "action": "buy",
            "product_id": product_id,
            "option_id": option_id,
            "duration": duration,
            "quantity": 1
        }

        provider_res = requests.post(
            PROVIDER_URL,
            headers=headers,
            data=payload,
            timeout=30
        )

        # Parse response safely
        try:
            res_json = provider_res.json()
        except Exception:
            res_json = {"raw_response": provider_res.text}

        # Check for license key in various standard API formats
        key_found = None
        if isinstance(res_json, dict):
            key_found = (
                res_json.get("key") or 
                res_json.get("license_key") or 
                res_json.get("serial") or
                res_json.get("code") or
                (res_json.get("data") and isinstance(res_json["data"], dict) and (
                    res_json["data"].get("key") or 
                    res_json["data"].get("license_key") or
                    res_json["data"].get("serial")
                )) or
                (isinstance(res_json.get("data"), list) and len(res_json["data"]) > 0 and res_json["data"][0])
            )

        if key_found:
            return jsonify({
                "status": "success",
                "key": str(key_found).strip(),
                "duration": duration,
                "product_id": product_id
            }), 200

        # Handle specific provider error messages
        error_msg = "Provider Error: Unable to issue key at this moment."
        if isinstance(res_json, dict):
            if "msg" in res_json:
                error_msg = res_json["msg"]
            elif "message" in res_json:
                error_msg = res_json["message"]
            elif "error" in res_json:
                error_msg = res_json["error"]

        return jsonify({
            "status": "error",
            "message": error_msg,
            "provider_response": res_json
        }), 400

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "message": "Server Timeout: Provider took too long to respond. Please retry."
        }), 504
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server Problem: {str(e)}"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
