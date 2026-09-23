import os
import re
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

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "service": "SAHARAJ EXE Universal Key Backend",
        "status": "online"
    }), 200

@app.route("/api/buy", methods=["POST"])
def buy_key():
    try:
        req_data = request.get_json() or {}
        
        # 1. Product ID
        product_id = str(req_data.get("product_id") or "133").strip()
        
        # 2. Raw Duration / Provider value
        raw_duration = str(req_data.get("duration") or "1 Hours").strip()
        cleaned_duration = re.sub(r'\[.*?\]', '', raw_duration).strip()
        
        # 3. Dynamic Option ID (Line 1 = 1, Line 2 = 2, etc.)
        option_id = str(req_data.get("option_id") or "1").strip()

        headers = {
            "x-master-key": MASTER_KEY,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json"
        }

        payload = {
            "api_key": RESELLER_API_KEY,
            "action": "buy",
            "product_id": product_id,
            "option_id": option_id,
            "duration": cleaned_duration,
            "quantity": 1
        }

        provider_res = requests.post(
            PROVIDER_URL,
            headers=headers,
            data=payload,
            timeout=30
        )

        try:
            res_json = provider_res.json()
        except Exception:
            res_json = {"raw_response": provider_res.text}

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
                (isinstance(res_json.get("data"), list) and len(res_json["data"]) > 0 and (
                    res_json["data"][0].get("key") if isinstance(res_json["data"][0], dict) else res_json["data"][0]
                ))
            )

        if key_found:
            return jsonify({
                "status": "success",
                "key": str(key_found).strip(),
                "duration": cleaned_duration,
                "product_id": product_id
            }), 200

        error_msg = "Provider issue: Unable to generate key"
        if isinstance(res_json, dict):
            error_msg = res_json.get("msg") or res_json.get("message") or res_json.get("error") or str(res_json)

        return jsonify({
            "status": "error",
            "message": error_msg,
            "provider_response": res_json
        }), 400

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error",
            "message": "Provider request timed out. Please retry."
        }), 504
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server Problem: {str(e)}"
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
