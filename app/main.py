from flask import Flask, jsonify, send_from_directory
from recommender import recommend_tests

app = Flask(__name__)

@app.route("/")
def home():
    return send_from_directory('.','index.html')

@app.route("/recommend/<int:user_id>")
def recommend(user_id):
    return jsonify({
       "user_id": user_id,
    "recommended_tests": result["recommended_tests"],
    "weak_areas": result["weak_areas"],
    "reason": result["reason"]
    })
import os
port = int(os.environ.get("PORT",5000))
app.run(host="0.0.0.0", port=5000)