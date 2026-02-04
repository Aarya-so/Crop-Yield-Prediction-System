from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np

app = Flask(__name__)
CORS(app)   # allow React requests

# 🔹 Load trained ML model
with open("crop_recommendation_modelrf.pkl", "rb") as file:
    model = pickle.load(file)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    # 🔹 Extract inputs (same names as frontend)
    nitrogen = float(data["nitrogen"])
    phosphorus = float(data["phosphorus"])
    potassium = float(data["potassium"]) 
    temperature = float(data["temperature"])
    humidity = float(data["humidity"])
   
    
    

    # 🔹 Arrange input in SAME ORDER as training
    input_data = np.array([[nitrogen, phosphorus, potassium, temperature, humidity]])

    # 🔹 Predict crop
    prediction = model.predict(input_data)[0]

    return jsonify({
        "recommended_crop": prediction
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
