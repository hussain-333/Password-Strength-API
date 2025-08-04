import json
import os
from datetime import datetime

USAGE_FILE = 'usage_tracker.json'

def load_usage():
    if not os.path.exists(USAGE_FILE) or os.stat(USAGE_FILE).st_size == 0:
        return {}
    with open(USAGE_FILE, 'r') as f:
        return json.load(f)


def save_usage(data):
    with open(USAGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_current_month():
    return datetime.now().strftime("%Y-%m")

def is_within_limit(api_key, tier_limits):
    usage = load_usage()
    current_month = get_current_month()
    key_usage = usage.get(api_key, {"month": current_month, "count": 0})

    # Reset count if month has changed
    if key_usage["month"] != current_month:
        key_usage = {"month": current_month, "count": 0}

    # Get limit for this key
    limit_str = tier_limits.get(api_key)
    if not limit_str:
        return False

    limit = int(limit_str.split()[0])
    if key_usage["count"] >= limit:
        return False

    key_usage["count"] += 1
    usage[api_key] = key_usage
    save_usage(usage)
    return True
