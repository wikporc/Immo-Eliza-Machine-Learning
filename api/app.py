import gradio as gr
import json
import requests

API_URL = "http://127.0.0.1:8010/predict"

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

# convert sets to sorted lists
for reg in regions:
    for prov in regions[reg]:
        regions[reg][prov] = sorted(list(regions[reg][prov]))

# ==========================================
# MAPPING DICTIONARIES USED BY MODEL
# ==========================================

state_grouped_mapping = {
    "To renovate": 0, "To be renovated": 0, "To restore": 0, "To demolish": 0,
    "Under construction": 1,
    "Normal": 2,
    "Fully renovated": 3, "Excellent": 3,
    "New": 4,
    "Missing": -1
}

kitchen_equipped_mapping = {
    "Missing": -1,
    "Not equipped": 0,
    "Partially equipped": 1,
    "Fully equipped": 2,
    "Super equipped": 3
}

glazing_mapping = {
    "Missing": -1,
    "Simple glass": 0,
    "Double glass": 1,
    "Triple glass": 2
}

heating_mapping = {
    "Missing": -1,
    "Not specified": -1,
    "Coal": 0, "Wood": 1, "Fuel oil": 2,
    "Gas": 3, "Hot air": 4,
    "Electricity": 5,
    "Solar energy": 6
}

flooding_mapping = {
    "no flooding area": 1,
    "Low risk": 1,
    "(information not available)": 0
}

# ===============================================================
# DROPDOWN UPDATE FUNCTIONS
# ===============================================================

def update_provinces(region):
    if not region:
        return gr.update(choices=[], value=None), gr.update(choices=[], value=None)
    provinces = sorted(regions[region].keys())
    return gr.update(choices=provinces, value=None), gr.update(choices=[], value=None)


def update_municipalities(region, province):
    if not region or not province:
        return gr.update(choices=[], value=None)
    municipalities = regions[region][province]
    return gr.update(choices=municipalities, value=None)


# ===============================================================
# API CALL
# ===============================================================

def prepare_payload(basic, advanced):
    region, province, municipality, rooms, area, property_type = basic

    payload = {
        "rooms": rooms,
        "area": area,
        "locality": municipality.lower(),
        "property_type": property_type,
        "property_subtype": property_type
    }

    (
        state, facades_number, is_furnished, has_terrace, has_garden,
        has_swimming_pool, kitchen, build_year, cellar, garage,
        bathrooms, heating, terrace_surface, sewer_connection, running_water,
        primary_energy_consumption, co2, cert_elec, preemption_right,
        flooding, leased, living_room_surface, glazing,
        elevator, entry_phone, access_disabled, apartement_floor,
        number_floors, toilets
    ) = advanced

    # Mapped fields (string → numeric)
    mapped_fields = {
        "state": state_grouped_mapping.get(state) if state else None,
        "has_equipped_kitchen": kitchen_equipped_mapping.get(kitchen) if kitchen else None,
        "glazing_type": glazing_mapping.get(glazing) if glazing else None,
        "heating_type": heating_mapping.get(heating) if heating else None,
        "flooding_area_type": flooding_mapping.get(flooding) if flooding else None,
    }

    # Regular optional fields
    other_fields = {
        "facades_number": facades_number,
        "is_furnished": int(is_furnished) if is_furnished is not None else None,
        "has_terrace": int(has_terrace) if has_terrace is not None else None,
        "has_garden": int(has_garden) if has_garden is not None else None,
        "has_swimming_pool": int(has_swimming_pool) if has_swimming_pool is not None else None,
        "build_year": build_year,
        "cellar": int(cellar) if cellar is not None else None,
        "garage": int(garage) if garage is not None else None,
        "bathrooms": bathrooms,
        "terrace_surface": terrace_surface,
        "sewer_connection": int(sewer_connection) if sewer_connection is not None else None,
        "running_water": int(running_water) if running_water is not None else None,
        "primary_energy_consumption": primary_energy_consumption,
        "co2": co2,
        "certification_electrical_installation": cert_elec,
        "preemption_right": int(preemption_right) if preemption_right is not None else None,
        "leased": int(leased) if leased is not None else None,
        "living_room_surface": living_room_surface,
        "elevator": int(elevator) if elevator is not None else None,
        "entry_phone": int(entry_phone) if entry_phone is not None else None,
        "access_disabled": int(access_disabled) if access_disabled is not None else None,
        "apartement_floor": apartement_floor,
        "number_floors": number_floors,
        "toilets": toilets,
    }

    # Merge and filter out None
    for k, v in mapped_fields.items():
        if v is not None:
            payload[k] = v

    for k, v in other_fields.items():
        if v is not None:
            payload[k] = v

    return payload


def predict_api(basic_inputs, advanced_inputs):
    payload = prepare_payload(basic_inputs, advanced_inputs)

    try:
        r = requests.post(API_URL, json=payload)
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
# GRADIO MULTI-PAGE (TABS)
# ===============================================================

with gr.Blocks(title="Immo Eliza ML") as demo:

    gr.Markdown("## Immo Eliza – Real Estate Price Prediction")

    # --- STATES ---
    basic_state = gr.State()
    advanced_state = gr.State()

    with gr.Tabs():

        # ===========================
        # TAB 1 – BASIC INPUTS
        # ===========================
        with gr.Tab("Basic Inputs"):

            gr.Markdown("### Step 1: Select Location")

            region_dd = gr.Dropdown(sorted(regions.keys()), label="Region")
            province_dd = gr.Dropdown([], label="Province")
            municipality_dd = gr.Dropdown([], label="Municipality")

            region_dd.change(update_provinces, region_dd, [province_dd, municipality_dd])
            province_dd.change(update_municipalities, [region_dd, province_dd], municipality_dd)

            gr.Markdown("### Step 2: Property basics")

            rooms = gr.Slider(1, 12, step=1, value=3, label="Rooms")
            area = gr.Slider(20, 700, step=1, value=80, label="Area (m²)")

            property_type = gr.Radio(["apartment", "house"], value="apartment", label="Property Type")

            def store_basic(*vals):
                return list(vals)

            store_basic_btn = gr.Button("Save Basic Inputs")
            store_basic_btn.click(
                store_basic,
                inputs=[region_dd, province_dd, municipality_dd, rooms, area, property_type],
                outputs=basic_state
            )

        # ===========================
        # TAB 2 – ADVANCED INPUTS
        # ===========================
        with gr.Tab("Advanced Features (Optional)"):

            gr.Markdown("### Fill any fields you want the model to use")

            # Numeric or dropdown fields
            state = gr.Dropdown(
            list(state_grouped_mapping.keys()),
            label="Property condition",
            value=None
            )
            facades_number = gr.Number(label="Facades Number", value=None)
            is_furnished = gr.Checkbox(label="Is Furnished?")
            has_terrace = gr.Checkbox(label="Terrace")
            has_garden = gr.Checkbox(label="Garden")
            has_swimming_pool = gr.Checkbox(label="Swimming Pool")
            has_equipped_kitchen = gr.Dropdown(
                list(kitchen_equipped_mapping.keys()),
                label="Kitchen equipment level",
                value=None
            )
            build_year = gr.Number(label="Build Year")
            cellar = gr.Checkbox(label="Cellar")
            garage = gr.Checkbox(label="Garage")
            bathrooms = gr.Number(label="Bathrooms")
            heating_type = gr.Dropdown(
                list(heating_mapping.keys()),
                label="Heating type",
                value=None
            )

            terrace_surface = gr.Number(label="Terrace Surface")
            sewer_connection = gr.Checkbox(label="Sewer Connection")
            running_water = gr.Checkbox(label="Running Water")
            primary_energy_consumption = gr.Number(label="Energy Consumption")
            co2 = gr.Number(label="CO₂ Emissions")
            cert_elec = gr.Number(label="Electrical Certificate")
            preemption_right = gr.Checkbox(label="Preemption Right")
            flooding_area_type = gr.Dropdown(
                list(flooding_mapping.keys()),
                label="Flooding risk",
                value=None
            )

            leased = gr.Checkbox(label="Leased?")
            living_room_surface = gr.Number(label="Living Room Surface")
            glazing_type = gr.Dropdown(
                list(glazing_mapping.keys()),
                label="Window glazing type",
                value=None
            )

            elevator = gr.Checkbox(label="Elevator")
            entry_phone = gr.Checkbox(label="Entry Phone")
            access_disabled = gr.Checkbox(label="Disability Access")
            apartement_floor = gr.Number(label="Floor")
            number_floors = gr.Number(label="Total Floors")
            toilets = gr.Number(label="Toilets")

            def store_adv(*vals):
                return list(vals)

            save_adv_btn = gr.Button("Save Advanced Inputs")
            save_adv_btn.click(
                store_adv,
                inputs=[
                    state, facades_number, is_furnished, has_terrace, has_garden,
                    has_swimming_pool, has_equipped_kitchen, build_year, cellar, garage,
                    bathrooms, heating_type, terrace_surface, sewer_connection, running_water,
                    primary_energy_consumption, co2, cert_elec, preemption_right,
                    flooding_area_type, leased, living_room_surface, glazing_type,
                    elevator, entry_phone, access_disabled, apartement_floor,
                    number_floors, toilets
                ],
                outputs=advanced_state
            )

    # ===============================================================
    # PREDICT BUTTON
    # ===============================================================
    predict_btn = gr.Button("Predict Price", variant="primary")
    result_box = gr.Textbox(label="Prediction Result")

    predict_btn.click(
        predict_api,
        inputs=[basic_state, advanced_state],
        outputs=result_box
    )


demo.launch()
