from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BASE_URL = "https://privateaadhar.anshppt19.workers.dev/?query="

@app.route("/", methods=["GET"])
def query():
    q = request.args.get("query")
    if not q:
        return jsonify({"error": "Please provide ?query= parameter"}), 400

    try:
        # original API se data fetch karo
        resp = requests.get(BASE_URL + q)
        data = resp.json()

        # ❌ remove unwanted fields
        for key in ["Buy Api", "NumOfResults", "NumOfDatabase", "search time"]:
            data.pop(key, None)

        # ✅ Owner field add karo
        data["Owner"] = "Saksham"

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)