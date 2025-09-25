from flask import Flask, request, jsonify
import requests
import re
import urllib.parse

app = Flask(__name__)

# Original API
ORIGINAL_API_BASE = "https://privateaadhar.anshppt19.workers.dev/?query="

# Keys / values to filter out
BANNED_KEYS = {"Buy Api", "List", "NumOfResults", "NumOfDatabase", "search time"}
BANNED_VALUE_SUBSTRINGS = ["@anshapi"]
BANNED_LIST_ROOT_NAMES = {"List"}


def looks_like_indian_10digit(s: str) -> bool:
    return bool(re.fullmatch(r"\d{10}", s.strip()))


def call_original_api(query: str):
    q = urllib.parse.quote(query, safe="")
    url = ORIGINAL_API_BASE + q
    resp = requests.get(url, timeout=15)
    try:
        return resp.json()
    except ValueError:
        return {"raw": resp.text}


def sanitize_obj(obj):
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            if k in BANNED_KEYS or k.lower() in {bk.lower() for bk in BANNED_KEYS}:
                continue
            if k in BANNED_LIST_ROOT_NAMES:
                continue
            sanitized_v = sanitize_obj(v)
            if isinstance(sanitized_v, str):
                if any(sub.lower() in sanitized_v.lower() for sub in BANNED_VALUE_SUBSTRINGS):
                    continue
            if isinstance(sanitized_v, (int, float)):
                if k.lower().startswith("num") and sanitized_v == 1:
                    continue
            new[k] = sanitized_v
        if "Owner" not in new:
            new["Owner"] = "Saksham"
        return new
    elif isinstance(obj, list):
        new_list = []
        for item in obj:
            sanitized_item = sanitize_obj(item)
            if isinstance(sanitized_item, str):
                if any(sub.lower() in sanitized_item.lower() for sub in BANNED_VALUE_SUBSTRINGS):
                    continue
            new_list.append(sanitized_item)
        return new_list
    elif isinstance(obj, str):
        if any(sub.lower() in obj.lower() for sub in BANNED_VALUE_SUBSTRINGS):
            return ""
        return obj
    else:
        return obj


# 👉 Root URL pe ?query= param expect karega
@app.route("/", methods=["GET"])
def query_api():
    q = request.args.get("query")
    if not q:
        return jsonify({"error": "Use ?query=...", "Owner": "Saksham"}), 400

    q = q.strip()
    if looks_like_indian_10digit(q):
        call_q = "+91" + q
    else:
        call_q = q

    try:
        original_resp = call_original_api(call_q)
    except requests.RequestException as e:
        return jsonify({"error": "Failed to reach original API", "details": str(e), "Owner": "Saksham"}), 502

    sanitized = sanitize_obj(original_resp)
    if isinstance(sanitized, dict):
        for banned in list(BANNED_KEYS):
            sanitized.pop(banned, None)
        sanitized.setdefault("Owner", "Saksham")
    return jsonify(sanitized)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)