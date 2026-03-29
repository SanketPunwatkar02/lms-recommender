from flask import Flask, jsonify, send_from_directory, request
from recommender import recommend_tests, add_user_data, get_test_options
import json

app = Flask(__name__)

@app.route("/")
def home():
    return send_from_directory('.','index.html')

@app.route("/recommend/<int:user_id>")
def recommend(user_id):
    result = recommend_tests(user_id)
    return jsonify({
       "user_id": user_id,
    "recommended_tests": result["recommended_tests"],
    "weak_areas": result["weak_areas"],
    "reason": result["reason"],
    "explanation": result.get("explanation", "")
    })

@app.route("/test-options")
def test_options():
    return jsonify(get_test_options())

@app.route("/submit-data", methods=["POST"])
def submit_data():
    try:
        data = request.get_json()
        result = add_user_data(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)