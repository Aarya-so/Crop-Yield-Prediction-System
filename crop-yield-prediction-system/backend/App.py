from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allows React to talk to Flask

@app.route("/predict", methods=["POST"])
def predict_crop():
    data = request.json

    temperature = data.get("temperature")
    humidity = data.get("humidity")
    n = data.get("nitrogen")
    p = data.get("phosphorus")
    k = data.get("potassium")

    # 🔹 Dummy logic (replace with ML later)
    if temperature > 25 and humidity > 100:
        crop = "Rice"
    elif temperature < 20:
        crop = "Wheat"
    else:
        crop = "Maize"

    return jsonify({
        "recommended_crop": crop
    })

if __name__ == "__main__":
    app.run(debug=True)
