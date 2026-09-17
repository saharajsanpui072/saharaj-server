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
DEFAULT_PRODUCT_ID = 133

# Duration / Option exact mapping for Provider API
DURATION_MAP = {
    "1 Hour": "1 Hours",
    "1 Hours": "1 Hours",
    "3 Hours": "3 Hours",
    "6 Hours": "6 Hours",
    "12 Hours": "12 Hours",
    "1 Day": "1 Days",
    "1 Days": "1 Days",
    "3 Days": "3 Days",
    "7 Days": "7 Days"
}

OPTION_ID_MAP = {
    "1 Hours": 1,
    "3 Hours": 2,
    "6 Hours": 3,
    "12 Hours": 4,
    "1 Days": 5,
    "3 Days": 6,
    "7 Days": 7
}

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "service": "SAHARAJ EXE Backend Proxy",
        "status": "online",
        "uptime": "24/7 Active"
    }), 200

@app.route("/api/buy", methods=["POST"])
def buy_key():
    try:
        req_data = request.get_json() or {}
        
        raw_duration = req_data.get("duration", "1 Hours")
        product_id = req_data.get("product_id", DEFAULT_PRODUCT_ID)
        
        # Match sanitized duration
        matched_duration = DURATION_MAP.get(raw_duration, raw_duration)
        option_id = req_data.get("option_id") or OPTION_ID_MAP.get(matched_duration, 1)

        headers = {
            "x-master-key": MASTER_KEY,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

        # Try sending form-encoded first as required by standard reseller PHP endpoints
        payload = {
            "api_key": RESELLER_API_KEY,
            "action": "buy",
            "product_id": str(product_id),
            "option_id": str(option_id),
            "duration": matched_duration,
            "quantity": 1
        }

        provider_res = requests.post(
            PROVIDER_URL,
            headers=headers,
            data=payload,
            timeout=25
        )

        # Parse response
        try:
            res_json = provider_res.json()
        except Exception:
            res_json = {"raw_response": provider_res.text}

        # Check for successful license key issuance
        key_found = None
        if isinstance(res_json, dict):
            key_found = (
                res_json.get("key") or 
                res_json.get("license_key") or 
                res_json.get("serial") or
                (res_json.get("data") and isinstance(res_json["data"], dict) and res_json["data"].get("key"))
            )

        if key_found:
            return jsonify({
                "status": "success",
                "key": key_found,
                "duration": matched_duration
            }), 200

        # Handle specific provider error message
        error_msg = "Server Problem: Unable to purchase key at this moment."
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
            "message": "Server Problem: Provider request timed out. Please try again."
        }), 504
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server Problem: {str(e)}"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
