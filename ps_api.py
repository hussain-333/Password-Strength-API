from usage_tracker import is_within_limit
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import hashlib
import requests
import math
import secrets
import json
import os

app = Flask(__name__)
CORS(app)

# --- Load API keys from file ---
if os.path.exists('api_keys.json'):
    with open('api_keys.json', 'r') as f:
        API_KEYS = json.load(f)
else:
    API_KEYS = {}

# --- Tier limits per month ---
TIER_LIMITS = {
    "free": "100 per month",
    "pro": "50000 per month",
    "ultra": "100000 per month",
    "mega": "5000000 per month"
}

# --- Helper: Get tier from API key ---
def get_tier_from_key(api_key):
    return API_KEYS.get(api_key)

# --- Password breach check using HaveIBeenPwned ---
def is_password_pwned(password):
    sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix = sha1_password[:5]
    suffix = sha1_password[5:]
    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    response = requests.get(url)
    if response.status_code != 200:
        return False, None
    hashes = response.text.splitlines()
    for line in hashes:
        hash_suffix, count = line.split(':')
        if hash_suffix == suffix:
            return True, int(count)
    return False, 0

# --- Entropy calculation ---
def calculate_entropy(password):
    charsets = 0
    if re.search(r'[a-z]', password): charsets += 26
    if re.search(r'[A-Z]', password): charsets += 26
    if re.search(r'\d', password): charsets += 10
    if re.search(r'[!@#$%^&*()_+\-=\[\]{};\'\\:"|<,./<>?]', password): charsets += 32
    charsets = max(charsets, 1)
    entropy = math.log2(charsets) * len(password)
    return round(entropy, 2)

# --- Crack time estimation ---
def estimate_crack_time(entropy):
    guesses_per_second = 1e9
    seconds = 2 ** entropy / guesses_per_second
    if seconds < 1:
        return "<1 second"
    elif seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours"
    elif seconds < 31536000:
        return f"{int(seconds / 86400)} days"
    else:
        return f"{round(seconds / 31536000, 1)} years"

# --- Strength evaluation ---
def check_password_strength(password):
    score = 0
    feedback = []

    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Make your password at least 8 characters long.")
    if re.search(r'[A-Z]', password) and re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Use both uppercase and lowercase letters.")
    if re.search(r'[0-9]', password):
        score += 1
    else:
        feedback.append("Include at least one number.")
    if re.search(r'[@$!%*#?&]', password):
        score += 1
    else:
        feedback.append("Include at least one special character like @$!%*#?&")
    if not any(pattern in password.lower() for pattern in ['1234', 'password', 'qwerty']):
        score += 1
    else:
        feedback.append("Avoid common patterns like '1234' or 'password'.")

    pwned, count = is_password_pwned(password)
    if pwned:
        feedback.append(f"This password has been found in data breaches {count} times. Avoid using it.")
        score -= 1

    score = max(0, min(score, 5))
    rating = "Weak" if score <= 2 else "Moderate" if score == 3 else "Strong"
    entropy = calculate_entropy(password)
    crack_time = estimate_crack_time(entropy)

    return {
        'score': score,
        'rating': rating,
        'feedback': feedback,
        'pwned': pwned,
        'pwned_count': count if pwned else 0,
        'entropy': entropy,
        'estimated_crack_time': crack_time
    }

# --- Endpoint with tier-based rate limit ---
@app.route('/check_password', methods=['POST'])
def check_password():
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key not in API_KEYS:
        return jsonify({"error": "Unauthorized or missing API key"}), 401

    # --- Usage limit check ---
    if not is_within_limit(api_key, {key: TIER_LIMITS[val] for key, val in API_KEYS.items()}):
        return jsonify({"error": "Monthly usage limit exceeded"}), 429

    data = request.get_json()
    password = data.get("password") if data else None

    if not password or not isinstance(password, str):
        return jsonify({"error": "Password is required and must be a string"}), 400

    result = check_password_strength(password)
    return jsonify(result)

# --- Random API key generator (run manually when needed) ---
def generate_api_key(length=32):
    return secrets.token_hex(length // 2)

if __name__ == '__main__':
    app.run(debug=True)
