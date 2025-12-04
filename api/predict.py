import numpy as np
import pandas as pd
import json
import joblib
from pathlib import Path




FEATURES_APT_JSON = r"models_optimisation\raw_features\raw_features_apt.json"
FEATURES_HOU_JSON = r"models_optimisation\raw_features\raw_features_house.json"

MODEL_PATH_APT = r"models_optimisation\cat_res_apt_BEST.pkl"
MODEL_PATH_HOU = r"models_optimisation\cat_res_house_BEST.pkl"

REQUIRED_FIELDS = [
    "rooms",
    "area",
    "locality",
    "property_type",
    "property_subtype"
]


# ======================================
# LOAD RAW FEATURE LISTS 
# ======================================

def load_feature_list(json_path):
    json_path = Path(json_path)
    if not json_path.exists():
        raise FileNotFoundError(f"Missing features JSON: {json_path}")

    with open(json_path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"JSON must contain a plain list, got: {type(data)}")

    return data


RAW_FEATURES_APT = load_feature_list(FEATURES_APT_JSON)
RAW_FEATURES_HOU = load_feature_list(FEATURES_HOU_JSON)


# ======================================
# MODEL LOADING
# ======================================

def load_model(path, label: str):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Missing model for {label}: {path}")
    return joblib.load(path)

MODEL_APT = load_model(MODEL_PATH_APT, "apartment")
MODEL_HOU = load_model(MODEL_PATH_HOU, "house")


# ======================================
# VALIDATION
# ======================================

def validate_input(data: dict):
    missing = [col for col in REQUIRED_FIELDS if col not in data]
    if missing:
        return False, f"Missing required fields: {missing}"

    if data["property_type"] not in ["apartment", "house"]:
        return False, "property_type must be 'apartment' or 'house'"

    return True, data


# ======================================
# PREPROCESSING (dynamic depending on type)
# ======================================

def preprocess_input(data: dict, prop_type: str) -> pd.DataFrame:
    if prop_type == "apartment":
        cols = RAW_FEATURES_APT
    else:
        cols = RAW_FEATURES_HOU

    row = {col: data.get(col, None) for col in cols}
    return pd.DataFrame([row])


# ======================================
# PREDICT LOGIC
# ======================================

def run_model(df: pd.DataFrame, prop_type: str) -> float:
    if prop_type == "apartment":
        model = MODEL_APT
    else:
        model = MODEL_HOU

    log_pred = model.predict(df)[0]
    return float(np.exp(log_pred))


# ======================================
# MAIN ENTRY
# ======================================

def predict(data: dict):
    ok, out = validate_input(data)
    if not ok:
        return {"status": "error", "prediction": None, "message": out}

    df = preprocess_input(out, out["property_type"])
    price = run_model(df, out["property_type"])

    return {
        "status": "ok",
        "prediction": price,
        "model_used": out["property_type"]
    }


"""# ======================================
# LOCAL TEST
# ======================================

if __name__ == "__main__":
    test = {
        "rooms": 2,
        "area": 75,
        "locality": "Gent",
        "property_type": "house",
        "property_subtype": "HOUSE",
        "bathrooms": 2
    }
    print(predict(test))
"""