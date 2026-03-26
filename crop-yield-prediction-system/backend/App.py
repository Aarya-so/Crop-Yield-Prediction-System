from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd
import torch
from torchvision import transforms
from PIL import Image
import io
import base64
from transformers import ViTForImageClassification

app = Flask(__name__)
CORS(app)

# ─── Load Crop Recommendation Model ───────────────────────────────────────────
with open("crop_recommendation_modelrf.pkl", "rb") as f:
    crop_model = pickle.load(f)

# ─── Load Fertilizer Models ────────────────────────────────────────────────────
with open("fertilizer_recommendation.pkl", "rb") as f:
    fertilizer_model = pickle.load(f)

with open("fertilizer_le.pkl", "rb") as f:
    fertilizer_le = pickle.load(f)

with open("fertilizer_columns.pkl", "rb") as f:
    fertilizer_columns = pickle.load(f)

# ─── Load Disease Model (ViT) ──────────────────────────────────────────────────
DISEASE_CLASSES = ["healthy", "leaf_curl", "leaf_spot", "whitefly", "yellowish"]  # update if different

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
disease_model = ViTForImageClassification.from_pretrained(
    'google/vit-base-patch16-224-in21k',
    num_labels=len(DISEASE_CLASSES),
    ignore_mismatched_sizes=True
)
disease_model.load_state_dict(torch.load("disease_prediction_model_torch.pth", map_location=device))
disease_model.to(device)
disease_model.eval()

disease_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/predict", methods=["POST"])
def predict_crop():
    data = request.get_json()
    nitrogen     = float(data["nitrogen"])
    phosphorus   = float(data["phosphorus"])
    potassium    = float(data["potassium"])
    temperature  = float(data["temperature"])
    humidity     = float(data["humidity"])

    input_data = np.array([[nitrogen, phosphorus, potassium, temperature, humidity]])
    prediction = crop_model.predict(input_data)[0]
    return jsonify({"recommended_crop": prediction})


@app.route("/fertilizer", methods=["POST"])
def predict_fertilizer():
    data = request.get_json()

    sample = pd.DataFrame([{
        "Soil_color":  data["soil_color"],
        "Nitrogen":    float(data["nitrogen"]),
        "Phosphorus":  float(data["phosphorus"]),
        "Potassium":   float(data["potassium"]),
        "pH":          float(data["ph"]),
        "Rainfall":    float(data["rainfall"]),
        "Temperature": float(data["temperature"]),
    }])

    # One-hot encode and align columns exactly as training
    sample = pd.get_dummies(sample)
    sample = sample.reindex(columns=fertilizer_columns, fill_value=0)

    prediction = fertilizer_model.predict(sample)
    fertilizer_name = fertilizer_le.inverse_transform(prediction)[0]
    return jsonify({"recommended_fertilizer": fertilizer_name})


@app.route("/disease", methods=["POST"])
def predict_disease():
    data = request.get_json()

    # Expect base64-encoded image
    image_data = data["image"]
    if "," in image_data:
        image_data = image_data.split(",")[1]

    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    input_tensor = disease_transforms(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = disease_model(input_tensor).logits
        probs = torch.nn.functional.softmax(outputs, dim=1)
        confidence, predicted_idx = torch.max(probs, 1)

    predicted_class = DISEASE_CLASSES[predicted_idx.item()]
    return jsonify({
        "disease": predicted_class,
        "confidence": round(confidence.item() * 100, 2)
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)