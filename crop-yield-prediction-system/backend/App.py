from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allows React to talk to Flask

@app.route("/predict", methods=["POST"])
def predict_crop():
    data = request.json

    temperature = data.get("temperature")
    rainfall = data.get("rainfall")
    soil_type = data.get("soilType")

    # 🔹 Dummy logic (replace with ML later)
    if temperature > 25 and rainfall > 100:
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
