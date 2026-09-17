import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # ওয়েবসাইটের ক্রস-অরিজিন রিকোয়েস্ট সাপোর্ট করার জন্য

# প্রোভাইডার কনফিগারেশন
PROVIDER_API_URL = "https://bantibhaiya.to/api/reseller_v1.php"
API_KEY = "f67105a05a812c45d3a5ffac39c58bd0"
MASTER_KEY = "a7f3e8b2c9d1f4a6b8c2d5e9f1a3b6c8"
DEFAULT_PRODUCT_PID = "133"

# ১. সার্ভার ২৪/৭ সচল ও Koyeb হেলথ চেক ঠিক রাখার রুট
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "service": "SAHARAJ EXE Backend Proxy",
        "uptime": "24/7 Active"
    }), 200

# ২. চাবি কেনার মূল API রুট
@app.route('/api/buy', methods=['POST'])
def buy_key():
    try:
        data = request.get_json() or {}
        
        # ফ্রন্টএন্ড থেকে আসা তথ্য
        product_id = data.get('product_id', DEFAULT_PRODUCT_PID)
        duration = data.get('duration')
        android_id = data.get('android_id', '0b9b969bc2e7997b')

        if not duration:
            return jsonify({"status": "error", "message": "Duration is required"}), 400

        # মূল ওয়েবসাইটে পাঠানোর পেলোড
        payload = {
            'api_key': API_KEY,
            'action': 'buy',
            'product_id': product_id,
            'duration': duration,
            'android_id': android_id
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-master-key': MASTER_KEY,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # মূল প্রোভাইডারে রিকোয়েস্ট পাঠানো
        response = requests.post(
            PROVIDER_API_URL,
            data=payload,
            headers=headers,
            timeout=25,
            verify=False
        )

        # রেসপন্স সরাসরি ফ্রন্টএন্ডে পাঠানো
        try:
            res_json = response.json()
            return jsonify(res_json), response.status_code
        except Exception:
            return jsonify({
                "status": "success" if response.status_code == 200 else "error",
                "raw_response": response.text
            }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({"status": "error", "message": "Provider API timeout"}), 504
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Koyeb এর জন্য পোর্ট এনভায়রনমেন্ট ভেরিয়েবল সেটআপ
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
