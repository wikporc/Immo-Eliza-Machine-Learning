import gradio as gr
import json
import requests

API_URL = "http://127.0.0.1:8010/predict"   # ustaw swój port

# ===============================================================
# LOAD LOCALITY MAP
# ===============================================================

LOCALITY_JSON_PATH = "locality_resolved_map_clean.json"

with open(LOCALITY_JSON_PATH, "r", encoding="utf-8") as f:
    locality_map = json.load(f)

# ===============================================================
# BUILD HIERARCHICAL STRUCTURE
# ===============================================================

regions = {}
for loc, info in locality_map.items():
    region = info["region"]
    province = info["province"]
    municipality = info["municipality"]

    regions.setdefault(region, {})
    regions[region].setdefault(province, set())
    regions[region][province].add(municipality)

# Konwersja do list dla dropdownów
for reg in regions:
    for prov in regions[reg]:
        regions[reg][prov] = sorted(list(regions[reg][prov]))


# ===============================================================
# API CALL
# ===============================================================

def call_api(region, province, municipality, rooms, area, property_type):
    if not all([region, province, municipality]):
        return "Select full location hierarchy."

    payload = {
        "rooms": rooms,
        "area": area,
        "locality": municipality.lower(),   # backend expects lowercase locality
        "property_type": property_type,
        "property_subtype": property_type
    }

    try:
        r = requests.post(API_URL, json=payload, timeout=10)
        if r.status_code != 200:
            return f"API error {r.status_code}: {r.text}"

        data = r.json()
        pred = data.get("prediction")

        if isinstance(pred, list):
            return f"Error: {pred}"
        return f"Estimated price: {pred:,.0f} EUR"

    except Exception as e:
        return f"Connection error: {e}"


# ===============================================================
# DROPDOWN UPDATE LOGIC
# ===============================================================

def update_provinces(region):
    if not region:
        return gr.update(choices=[], value=None), gr.update(choices=[], value=None)
    provinces = sorted(list(regions[region].keys()))
    return gr.update(choices=provinces, value=None), gr.update(choices=[], value=None)


def update_municipalities(region, province):
    if not region or not province:
        return gr.update(choices=[], value=None)
    municipalities = regions[region][province]
    return gr.update(choices=municipalities, value=None)


# ===============================================================
# BUILD UI
# ===============================================================

with gr.Blocks(title="Immo Eliza Price Predictor") as demo:

    gr.Markdown("## Real Estate Price Prediction")

    with gr.Row():
        region_dd = gr.Dropdown(
            label="Region", choices=sorted(regions.keys()), value=None
        )
        province_dd = gr.Dropdown(label="Province", choices=[], value=None)
        municipality_dd = gr.Dropdown(label="Municipality", choices=[], value=None)

    region_dd.change(fn=update_provinces, 
                     inputs=region_dd, 
                     outputs=[province_dd, municipality_dd])

    province_dd.change(fn=update_municipalities,
                       inputs=[region_dd, province_dd],
                       outputs=municipality_dd)

    with gr.Row():
        rooms = gr.Slider(1, 10, step=1, value=3, label="Rooms")
        area = gr.Slider(20, 600, step=1, value=80, label="Area (m²)")

    property_type = gr.Radio(
        ["apartment", "house"],
        label="Property Type",
        value="apartment"
    )

    predict_btn = gr.Button("Predict Price ★")

    output = gr.Textbox(label="Result")

    predict_btn.click(
        fn=call_api,
        inputs=[region_dd, province_dd, municipality_dd, rooms, area, property_type],
        outputs=output
    )

demo.launch()
