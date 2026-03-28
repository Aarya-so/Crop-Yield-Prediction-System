from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import pandas as pd

app = Flask(__name__)
CORS(app)

# ─── Crop Recommendation (original model, unchanged) ──────────────────────────
with open("crop_recommendation_modelrf.pkl", "rb") as f:
    crop_rec_model = pickle.load(f)

# ─── Maharashtra Unified Models (yield + fertilizer) ──────────────────────────
# Shared inputs: crop, nitrogen, phosphorus, potassium,
#                temperature, humidity, moisture, ph
# Supported crops: cotton, maize, rice, soybean, sugarcane

with open("mh_yield_regressor.pkl",  "rb") as f: yield_model      = pickle.load(f)
with open("mh_yield_thresholds.pkl", "rb") as f: yield_thresholds = pickle.load(f)
with open("mh_fert_classifier.pkl",  "rb") as f: fert_model       = pickle.load(f)
with open("mh_fert_le.pkl",          "rb") as f: fert_le          = pickle.load(f)
with open("mh_crop_le.pkl",          "rb") as f: crop_le          = pickle.load(f)

# ─── Disease (ViT) — uncomment when .pth file is ready ────────────────────────
# import torch
# from torchvision import transforms
# from PIL import Image
# import io, base64
# from transformers import ViTForImageClassification
#
# DISEASE_CLASSES = ["healthy", "leaf_curl", "leaf_spot", "whitefly", "yellowish"]
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# disease_model = ViTForImageClassification.from_pretrained(
#     'google/vit-base-patch16-224-in21k',
#     num_labels=len(DISEASE_CLASSES), ignore_mismatched_sizes=True
# )
# disease_model.load_state_dict(
#     torch.load("disease_prediction_model_torch.pth", map_location=device)
# )
# disease_model.to(device); disease_model.eval()
# disease_transforms = transforms.Compose([
#     transforms.Resize((224, 224)), transforms.ToTensor(),
#     transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
# ])


# ─── ICAR Maharashtra NPK thresholds per crop ────────────────────────────────
# Used to generate validated, crop-specific explanations grounded in actual values
CROP_THRESHOLDS = {
    "rice":      dict(n_low=90,  p_low=40,  k_low=38,  n_high=110, p_high=52,  k_high=45,  n_opt="90–110", p_opt="40–52",  k_opt="38–45"),
    "sugarcane": dict(n_low=220, p_low=90,  k_low=115, n_high=260, p_high=108, k_high=138, n_opt="220–260",p_opt="90–108", k_opt="115–138"),
    "cotton":    dict(n_low=115, p_low=58,  k_low=46,  n_high=138, p_high=72,  k_high=55,  n_opt="115–138",p_opt="58–72",  k_opt="46–55"),
    "soybean":   dict(n_low=26,  p_low=66,  k_low=36,  n_high=34,  p_high=75,  k_high=45,  n_opt="26–34",  p_opt="66–75",  k_opt="36–45"),
    "maize":     dict(n_low=130, p_low=66,  k_low=46,  n_high=150, p_high=76,  k_high=55,  n_opt="130–150",p_opt="66–76",  k_opt="46–55"),
}

# Fertilizer composition reference
FERTILIZER_COMPOSITION = {
    "Urea":               "46% N",
    "DAP":                "18% N, 46% P₂O₅",
    "MOP":                "60% K₂O",
    "SSP":                "16% P₂O₅, 11% S",
    "Ammonium Sulphate":  "21% N, 24% S",
    "NPK 20-20-0":        "20% N, 20% P₂O₅",
    "NPK 15-15-15":       "15% N, 15% P₂O₅, 15% K₂O",
    "NPK 12-32-16":       "12% N, 32% P₂O₅, 16% K₂O",
    "NPK 14-35-14":       "14% N, 35% P₂O₅, 14% K₂O",
}

def build_explanation(crop, fertilizer, n, p, k, ph):
    """
    Generate a validated, crop-specific explanation grounded in actual input
    values vs ICAR Maharashtra guidelines. Every point cites real numbers.
    """
    t    = CROP_THRESHOLDS.get(crop, {})
    comp = FERTILIZER_COMPOSITION.get(fertilizer, "")
    cname = crop.capitalize()

    if not t:
        return [f"{fertilizer} ({comp})", "Recommended based on current soil conditions."]

    n_def  = n < t["n_low"]
    p_def  = p < t["p_low"]
    k_def  = k < t["k_low"]
    n_high = n >= t["n_high"]
    p_high = p >= t["p_high"]
    k_high = k >= t["k_high"]

    lines = []

    # ── Line 1: Fertilizer identity with composition ───────────────────────────
    lines.append(f"{fertilizer} ({comp}) — recommended for {cname} under current soil conditions.")

    # ── Line 2: NPK status vs ICAR optimal range ──────────────────────────────
    def status(val, low, high, opt, symbol):
        if val < low:   return f"N={val} kg/ha is below the ICAR-recommended minimum of {low} kg/ha for {cname} (optimal: {opt} kg/ha) — {symbol} deficient"
        if val >= high: return f"{symbol}={val} kg/ha is above the adequate range (optimal: {opt} kg/ha for {cname}) — sufficient"
        return f"{symbol}={val} kg/ha is within the adequate range (optimal: {opt} kg/ha for {cname})"

    n_status = f"N={n} kg/ha is {'below' if n_def else 'within' if not n_high else 'above'} the ICAR range of {t['n_opt']} kg/ha for {cname}"
    p_status = f"P={p} kg/ha is {'below' if p_def else 'within' if not p_high else 'above'} the ICAR range of {t['p_opt']} kg/ha for {cname}"
    k_status = f"K={k} kg/ha is {'below' if k_def else 'within' if not k_high else 'above'} the ICAR range of {t['k_opt']} kg/ha for {cname}"

    lines.append(f"Soil reading: {n_status}. {p_status}. {k_status}.")

    # ── Line 3: Primary reason this fertilizer was chosen ─────────────────────
    if fertilizer == "Urea":
        lines.append(f"Urea addresses the nitrogen shortfall. As a 46% N source, it is the most cost-effective way to bring N up to the {cname} requirement of {t['n_opt']} kg/ha.")
    elif fertilizer == "DAP":
        lines.append(f"DAP is prescribed because both N and P are below the {cname} minimum. It simultaneously supplies nitrogen and a high phosphorus dose (46% P₂O₅) to correct both deficiencies in a single application.")
    elif fertilizer == "MOP":
        lines.append(f"MOP targets the potassium deficit. With 60% K₂O, it efficiently restores K to the {cname} optimal range of {t['k_opt']} kg/ha, improving disease resistance and grain/fibre quality.")
    elif fertilizer == "SSP":
        lines.append(f"SSP corrects the phosphorus deficit (P={p} kg/ha vs minimum {t['p_low']} kg/ha for {cname}). It also supplies sulphur (11% S), which is commonly deficient in Maharashtra's Vertisol (black cotton) soils and improves P uptake efficiency.")
    elif fertilizer == "Ammonium Sulphate":
        lines.append(f"Ammonium Sulphate is recommended where nitrogen needs a boost alongside sulphur. For {cname} in Maharashtra's slightly alkaline soils (your pH={ph}), sulphur helps acidify the rhizosphere and improves overall nutrient availability.")
    elif fertilizer == "NPK 20-20-0":
        reasons = []
        if n_def: reasons.append(f"N is low ({n} vs minimum {t['n_low']} kg/ha)")
        if p_def: reasons.append(f"P is low ({p} vs minimum {t['p_low']} kg/ha)")
        if not reasons: reasons.append(f"N and P are approaching the lower bound of the {cname} optimal range")
        lines.append(f"NPK 20-20-0 provides a balanced N+P correction: {' and '.join(reasons)}. No additional potassium is needed since K={k} kg/ha is adequate for {cname}.")
    elif fertilizer == "NPK 15-15-15":
        lines.append(f"A fully balanced NPK formulation is appropriate when all three macronutrients need replenishment or maintenance. For {cname}, the ICAR-recommended ranges are N:{t['n_opt']}, P:{t['p_opt']}, K:{t['k_opt']} kg/ha — your soil values are approaching the lower bounds across the board.")
    elif fertilizer in ("NPK 12-32-16", "NPK 14-35-14"):
        lines.append(f"This high-P formulation is chosen because phosphorus demand for {cname} is disproportionately high relative to nitrogen. With P={p} kg/ha already above adequate levels and the crop's P:N ratio at {round(p/max(n,1),2)}, a P-weighted blend ensures the correct nutrient balance without over-applying nitrogen.")

    # ── Line 4: pH note if relevant ────────────────────────────────────────────
    if ph < 6.0:
        lines.append(f"Note: Soil pH={ph} is below 6.0. Acidic conditions reduce phosphorus availability — consider liming to bring pH into the {cname} optimal range (6.0–7.0) for full fertilizer effectiveness.")
    elif ph > 7.5:
        lines.append(f"Note: Soil pH={ph} is above 7.5. Alkaline conditions can lock up micronutrients and reduce N availability — sulphur-containing fertilizers (like this one) or gypsum can help correct pH over time.")

    return lines


def build_mh_input(data):
    """Build the shared 8-feature input array for yield + fertilizer models."""
    crop = data["crop"].strip().lower()
    if crop not in crop_le.classes_:
        return None, crop
    crop_enc = crop_le.transform([crop])[0]
    arr = np.array([[
        crop_enc,
        float(data["nitrogen"]),
        float(data["phosphorus"]),
        float(data["potassium"]),
        float(data["temperature"]),
        float(data["humidity"]),
        float(data["moisture"]),
        float(data["ph"]),
    ]])
    return arr, crop


# ══════════════════════════════════════════════════════════════════════════════
# Routes
# ══════════════════════════════════════════════════════════════════════════════

# ─── Yield validation data ────────────────────────────────────────────────────
# Maharashtra state averages + ICAR attainable yield benchmarks
YIELD_BENCHMARKS = {
    "rice":      dict(state_avg=2437,  attainable=4500,  unit="kg/ha",  season="Kharif (Jun–Nov)"),
    "sugarcane": dict(state_avg=91000, attainable=120000, unit="kg/ha", season="Annual (planted Oct–Mar)"),
    "cotton":    dict(state_avg=450,   attainable=800,   unit="kg/ha",  season="Kharif (Jun–Nov)"),
    "soybean":   dict(state_avg=1200,  attainable=2500,  unit="kg/ha",  season="Kharif (Jun–Oct)"),
    "maize":     dict(state_avg=2656,  attainable=6000,  unit="kg/ha",  season="Kharif / Rabi"),
}

# Which input is the biggest yield lever per crop (for limiting factor analysis)
YIELD_LEVERS = {
    "rice":      [("nitrogen", 90, 110), ("moisture", 60, 80), ("ph", 5.5, 7.0)],
    "sugarcane": [("nitrogen", 220, 260), ("moisture", 65, 80), ("potassium", 115, 138)],
    "cotton":    [("nitrogen", 115, 138), ("moisture", 40, 60), ("ph", 6.0, 8.0)],
    "soybean":   [("phosphorus", 66, 75), ("moisture", 50, 70), ("ph", 6.0, 7.5)],
    "maize":     [("nitrogen", 130, 150), ("moisture", 50, 70), ("potassium", 46, 55)],
}

def build_yield_validation(crop, yield_val, category, data):
    """Generate ICAR-grounded yield validation lines."""
    b = YIELD_BENCHMARKS.get(crop)
    t = CROP_THRESHOLDS.get(crop)
    if not b or not t:
        return []

    cname   = crop.capitalize()
    lines   = []
    pct_avg = round((yield_val / b["state_avg"] - 1) * 100, 1)
    pct_att = round((yield_val / b["attainable"]) * 100, 1)

    # Line 1: predicted vs state average
    direction = f"{abs(pct_avg)}% above" if pct_avg >= 0 else f"{abs(pct_avg)}% below"
    lines.append(
        f"Predicted yield of {yield_val:,.1f} {b['unit']} is {direction} the Maharashtra "
        f"state average of {b['state_avg']:,} {b['unit']} for {cname} ({b['season']})."
    )

    # Line 2: vs ICAR attainable yield
    lines.append(
        f"ICAR attainable yield benchmark for {cname} under optimal conditions is "
        f"{b['attainable']:,} {b['unit']}. Your field is currently at {pct_att}% of that potential."
    )

    # Line 3: category meaning in context
    thresh = yield_thresholds.get(crop, {})
    low_max  = round(thresh.get("low_max",  0), 1)
    high_min = round(thresh.get("high_min", 0), 1)
    if category == "High":
        lines.append(
            f"Category HIGH means your yield ({yield_val:,.1f}) exceeds {high_min:,} {b['unit']} — "
            f"the top 33rd percentile for {cname} in this model's Maharashtra dataset. "
            f"Soil and climate conditions are well-matched."
        )
    elif category == "Medium":
        lines.append(
            f"Category MEDIUM means your yield ({yield_val:,.1f}) falls between {low_max:,} and "
            f"{high_min:,} {b['unit']} — the middle third for {cname}. "
            f"Targeted improvements to limiting inputs can push this to High."
        )
    else:
        lines.append(
            f"Category LOW means your yield ({yield_val:,.1f}) is below {low_max:,} {b['unit']} — "
            f"the bottom 33rd percentile for {cname}. "
            f"Significant gains are possible with corrective fertilizer and moisture management."
        )

    # Line 4: limiting factor — which input is furthest below its optimal range
    levers = YIELD_LEVERS.get(crop, [])
    limiting = []
    for field, lo, hi in levers:
        val = float(data.get(field, 0))
        if val < lo:
            gap = round(lo - val, 1)
            limiting.append(f"{field} ({val} vs minimum {lo} — gap of {gap})")
    if limiting:
        lines.append(
            f"Primary limiting factor(s) identified: {'; '.join(limiting)}. "
            f"Addressing these is the fastest path to yield improvement."
        )
    else:
        lines.append(
            f"All key inputs (N, P, K, moisture, pH) are within or above the ICAR "
            f"optimal range for {cname}. Yield is limited mainly by natural variability."
        )

    return lines


# ─── Crop recommendation profiles ────────────────────────────────────────────
# All crops the original model supports, Maharashtra crops get richer detail
CROP_PROFILES = {
    # ── Maharashtra crops (rich detail) ───────────────────────────────────────
    "rice": dict(
        ideal_n=(80,120), ideal_p=(30,60), ideal_k=(30,50),
        ideal_temp=(25,35), ideal_hum=(75,90),
        season="Kharif (Jun–Nov)", soil="Clayey / loamy, water-retentive",
        maharashtra=True,
        note="Rice is the primary staple of Konkan and Vidarbha. High humidity and standing water conditions are critical for transplanting stage.",
    ),
    "sugarcane": dict(
        ideal_n=(200,280), ideal_p=(80,120), ideal_k=(100,150),
        ideal_temp=(27,35), ideal_hum=(70,85),
        season="Annual ratoon crop", soil="Deep black cotton soil (Vertisol)",
        maharashtra=True,
        note="Maharashtra is India's largest sugarcane producer. Western Maharashtra (Kolhapur, Pune, Ahmednagar) districts are most suitable.",
    ),
    "cotton": dict(
        ideal_n=(100,150), ideal_p=(50,80), ideal_k=(40,60),
        ideal_temp=(25,35), ideal_hum=(50,70),
        season="Kharif (Jun–Nov)", soil="Deep black cotton soil (Vertisol)",
        maharashtra=True,
        note="Vidarbha and Marathwada are Maharashtra's primary cotton belts. Bt-cotton varieties dominate. Well-drained black soil is essential.",
    ),
    "soybean": dict(
        ideal_n=(20,40), ideal_p=(60,80), ideal_k=(30,50),
        ideal_temp=(22,32), ideal_hum=(60,80),
        season="Kharif (Jun–Oct)", soil="Well-drained medium black soil",
        maharashtra=True,
        note="Maharashtra accounts for ~40% of India's soybean production. Marathwada and Vidarbha are key regions. Low N requirement since soybean fixes atmospheric N via root nodules.",
    ),
    "maize": dict(
        ideal_n=(120,160), ideal_p=(60,80), ideal_k=(40,60),
        ideal_temp=(22,32), ideal_hum=(55,75),
        season="Kharif / Rabi", soil="Loamy, well-drained red or black soil",
        maharashtra=True,
        note="Maize is grown across Nashik, Dhule, and Aurangabad districts. High nitrogen demand — adequate N is the single biggest yield lever for maize in Maharashtra.",
    ),
    # ── Other crops (standard profiles) ───────────────────────────────────────
    "wheat":     dict(ideal_n=(100,140), ideal_p=(50,80),  ideal_k=(40,60),  ideal_temp=(10,24), ideal_hum=(50,75), season="Rabi (Nov–Apr)",    soil="Loamy / clay loam", maharashtra=False, note="Cool temperatures during grain filling are critical. Avoid waterlogging."),
    "jute":      dict(ideal_n=(60,100),  ideal_p=(30,60),  ideal_k=(30,50),  ideal_temp=(24,34), ideal_hum=(75,95), season="Kharif",           soil="Alluvial, high moisture", maharashtra=False, note="Thrives in humid, warm conditions. Common in eastern India."),
    "coffee":    dict(ideal_n=(80,120),  ideal_p=(40,70),  ideal_k=(60,100), ideal_temp=(18,26), ideal_hum=(70,90), season="Perennial",        soil="Laterite / loamy", maharashtra=False, note="Shade-grown at higher altitudes. Western Ghats are primary growing region."),
    "tea":       dict(ideal_n=(80,120),  ideal_p=(30,60),  ideal_k=(40,80),  ideal_temp=(15,24), ideal_hum=(75,90), season="Perennial",        soil="Acidic loamy (pH 4.5–5.5)", maharashtra=False, note="Requires acidic soil and high rainfall. Assam and Darjeeling are primary regions."),
    "rubber":    dict(ideal_n=(60,100),  ideal_p=(30,60),  ideal_k=(60,100), ideal_temp=(22,30), ideal_hum=(75,90), season="Perennial",        soil="Laterite, well-drained", maharashtra=False, note="High humidity and warm climate essential. Kerala is the primary producer."),
    "banana":    dict(ideal_n=(100,200), ideal_p=(50,100), ideal_k=(200,400),ideal_temp=(20,30), ideal_hum=(70,90), season="Perennial (12–15 months)", soil="Rich loamy", maharashtra=False, note="Potassium-hungry crop. Requires frequent irrigation and warm temperatures."),
    "mango":     dict(ideal_n=(50,100),  ideal_p=(30,60),  ideal_k=(50,100), ideal_temp=(24,30), ideal_hum=(50,80), season="Perennial",        soil="Deep loamy, well-drained", maharashtra=False, note="Requires a dry spell before flowering. Alphonso variety dominates in Konkan Maharashtra."),
    "grapes":    dict(ideal_n=(40,80),   ideal_p=(30,60),  ideal_k=(60,120), ideal_temp=(15,35), ideal_hum=(40,70), season="Perennial",        soil="Light sandy loam", maharashtra=False, note="Nashik is India's wine capital. Requires dry conditions during ripening."),
    "watermelon":dict(ideal_n=(60,100),  ideal_p=(40,80),  ideal_k=(80,150), ideal_temp=(25,35), ideal_hum=(50,70), season="Summer (Feb–May)", soil="Sandy loam", maharashtra=False, note="High potassium requirement during fruiting. Sensitive to waterlogging."),
    "mungbean":  dict(ideal_n=(20,40),   ideal_p=(40,60),  ideal_k=(20,40),  ideal_temp=(25,35), ideal_hum=(60,80), season="Kharif / Zaid",   soil="Well-drained loamy", maharashtra=False, note="Short-duration legume. Low N requirement due to biological nitrogen fixation."),
    "blackgram": dict(ideal_n=(20,40),   ideal_p=(40,60),  ideal_k=(20,40),  ideal_temp=(25,35), ideal_hum=(60,80), season="Kharif / Rabi",   soil="Well-drained loamy", maharashtra=False, note="Similar to mungbean. Tolerates slightly acidic soils."),
    "lentil":    dict(ideal_n=(20,40),   ideal_p=(40,60),  ideal_k=(20,40),  ideal_temp=(18,25), ideal_hum=(50,70), season="Rabi (Oct–Mar)",  soil="Loamy, well-drained", maharashtra=False, note="Cool-season legume. Sensitive to waterlogging and high temperatures."),
    "pomegranate":dict(ideal_n=(50,100), ideal_p=(30,60),  ideal_k=(60,120), ideal_temp=(25,35), ideal_hum=(40,70), season="Perennial",       soil="Well-drained sandy loam", maharashtra=False, note="Drought-tolerant once established. Solapur and Nashik are key Maharashtra regions."),
    "orange":    dict(ideal_n=(80,120),  ideal_p=(30,60),  ideal_k=(80,120), ideal_temp=(20,30), ideal_hum=(50,80), season="Perennial",       soil="Deep loamy, well-drained", maharashtra=False, note="Vidarbha (Nagpur) is famous for its oranges. Requires well-drained soil and mild winters."),
    "papaya":    dict(ideal_n=(100,150), ideal_p=(50,100), ideal_k=(100,200),ideal_temp=(22,32), ideal_hum=(60,80), season="Perennial",       soil="Rich loamy, well-drained", maharashtra=False, note="Fast-growing fruit crop. Sensitive to frost and waterlogging."),
    "coconut":   dict(ideal_n=(50,100),  ideal_p=(30,60),  ideal_k=(150,300),ideal_temp=(25,35), ideal_hum=(70,90), season="Perennial",       soil="Sandy loam, coastal", maharashtra=False, note="Extremely high potassium demand. Coastal Konkan region is most suitable in Maharashtra."),
    "kidneybeans":dict(ideal_n=(20,40),  ideal_p=(40,70),  ideal_k=(30,60),  ideal_temp=(18,25), ideal_hum=(60,80), season="Rabi",           soil="Well-drained loamy", maharashtra=False, note="Cool-season legume. Fix atmospheric nitrogen. Avoid high N application."),
    "pigeonpeas":dict(ideal_n=(20,40),   ideal_p=(40,80),  ideal_k=(20,40),  ideal_temp=(25,35), ideal_hum=(60,80), season="Kharif",          soil="Well-drained medium soil", maharashtra=False, note="Tur/Arhar — major pulse crop in Maharashtra. Drought-tolerant and deep-rooted."),
    "mothbeans": dict(ideal_n=(20,40),   ideal_p=(30,60),  ideal_k=(20,40),  ideal_temp=(28,38), ideal_hum=(40,60), season="Kharif",          soil="Sandy, drought-prone", maharashtra=False, note="Extremely drought-tolerant. Suited to arid Rajasthan and parts of Marathwada."),
    "chickpea":  dict(ideal_n=(20,40),   ideal_p=(40,80),  ideal_k=(20,40),  ideal_temp=(15,25), ideal_hum=(40,65), season="Rabi (Oct–Mar)",  soil="Well-drained loamy / black", maharashtra=False, note="Harbhara — important rabi pulse. Cool dry weather at maturity is essential."),
}

def build_crop_validation(crop, n, p, k, temp, hum):
    """Generate agronomic suitability notes for the recommended crop."""
    profile = CROP_PROFILES.get(crop.lower())
    cname   = crop.capitalize()
    lines   = []

    if not profile:
        lines.append(f"{cname} was recommended based on your NPK, temperature, and humidity inputs.")
        return lines

    # Line 1: identity + season + soil
    mh_tag = " (major Maharashtra crop)" if profile["maharashtra"] else ""
    lines.append(
        f"{cname}{mh_tag} — {profile['season']}. Preferred soil: {profile['soil']}."
    )

    # Line 2: input match assessment
    matches, mismatches = [], []
    checks = [
        ("N", n,    *profile["ideal_n"]),
        ("P", p,    *profile["ideal_p"]),
        ("K", k,    *profile["ideal_k"]),
        ("Temp", temp, *profile["ideal_temp"]),
        ("Humidity", hum, *profile["ideal_hum"]),
    ]
    for label, val, lo, hi in checks:
        if lo <= val <= hi:
            matches.append(label)
        else:
            direction = "low" if val < lo else "high"
            mismatches.append(f"{label}={val} ({direction}, ideal {lo}–{hi})")

    if mismatches:
        lines.append(
            f"Your inputs largely match {cname} requirements. "
            f"Note: {'; '.join(mismatches)}."
        )
    else:
        lines.append(
            f"All inputs (N, P, K, temperature, humidity) are within the ideal "
            f"range for {cname}. Conditions are well-suited."
        )

    # Line 3: Maharashtra-specific or general agronomic note
    lines.append(profile["note"])

    return lines


# ── 1. Crop Recommendation ─────────────────────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict_crop():
    data       = request.get_json()
    n, p, k    = float(data["nitrogen"]), float(data["phosphorus"]), float(data["potassium"])
    temp, hum  = float(data["temperature"]), float(data["humidity"])
    inp        = np.array([[n, p, k, temp, hum]])
    prediction = crop_rec_model.predict(inp)[0]
    validation = build_crop_validation(prediction, n, p, k, temp, hum)
    return jsonify({
        "recommended_crop": prediction,
        "validation":       validation,
    })


# ── 2. Yield Prediction (Maharashtra, unified inputs) ──────────────────────────
@app.route("/yield", methods=["POST"])
def predict_yield():
    data = request.get_json()
    inp, crop = build_mh_input(data)
    if inp is None:
        return jsonify({
            "error": f"Unknown crop '{crop}'. Supported: {list(crop_le.classes_)}"
        }), 400

    yield_val = round(float(max(0, yield_model.predict(inp)[0])), 1)

    thresh = yield_thresholds.get(crop, {})
    if yield_val >= thresh.get("high_min", float("inf")):
        category = "High"
    elif yield_val <= thresh.get("low_max", 0):
        category = "Low"
    else:
        category = "Medium"

    return jsonify({
        "yield_kg_ha":    yield_val,
        "yield_category": category,
        "validation":     build_yield_validation(crop, yield_val, category, data),
    })


# ── 3. Fertilizer Recommendation (Maharashtra, unified inputs) ─────────────────
@app.route("/fertilizer", methods=["POST"])
def predict_fertilizer():
    data = request.get_json()
    inp, crop = build_mh_input(data)
    if inp is None:
        return jsonify({
            "error": f"Unknown crop '{crop}'. Supported: {list(crop_le.classes_)}"
        }), 400

    pred       = fert_model.predict(inp)
    fertilizer = fert_le.inverse_transform(pred)[0]
    explanation = build_explanation(
        crop       = crop,
        fertilizer = fertilizer,
        n          = float(data["nitrogen"]),
        p          = float(data["phosphorus"]),
        k          = float(data["potassium"]),
        ph         = float(data["ph"]),
    )
    return jsonify({
        "recommended_fertilizer": fertilizer,
        "explanation":            explanation,
    })


# ── 4. Disease Prediction (uncomment when model is ready) ─────────────────────
# @app.route("/disease", methods=["POST"])
# def predict_disease():
#     data = request.get_json()
#     image_data = data["image"]
#     if "," in image_data: image_data = image_data.split(",")[1]
#     image = Image.open(io.BytesIO(base64.b64decode(image_data))).convert("RGB")
#     inp = disease_transforms(image).unsqueeze(0).to(device)
#     with torch.no_grad():
#         logits = disease_model(inp).logits
#         probs  = torch.nn.functional.softmax(logits, dim=1)
#         conf, idx = torch.max(probs, 1)
#     return jsonify({
#         "disease":    DISEASE_CLASSES[idx.item()],
#         "confidence": round(conf.item() * 100, 2)
#     })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)