import gradio as gr
import requests
import json

API_URL = "http://127.0.0.1:8010/predict"

def call_api(rooms, area, locality, property_type, property_subtype):
    payload = {
        "rooms": rooms,
        "area": area,
        "locality": locality,
        "property_type": property_type,
        "property_subtype": property_subtype
    }

    try:
        r = requests.post(API_URL, json=payload)
        data = r.json()

        if data.get("status") != "ok":
            return f"Error: {data.get('message')}"

        price = data.get("prediction")
        return f"{price:,.0f} EUR"

    except Exception as e:
        return f"API error: {str(e)}"


with gr.Blocks() as demo:
    gr.Markdown("## Immo Eliza Price Prediction")

    with gr.Row():
        rooms = gr.Number(label="Rooms", value=3)
        area = gr.Number(label="Area (m²)", value=80)

    locality = gr.Textbox(label="Locality (city name)", value="Brussels")

    property_type = gr.Dropdown(
        ["apartment", "house"],
        value="apartment",
        label="Property Type"
    )

    property_subtype = gr.Textbox(label="Property Subtype", value="APARTMENT")

    out = gr.Textbox(label="Predicted Price", interactive=False)

    btn = gr.Button("Predict")
    btn.click(
        fn=call_api,
        inputs=[rooms, area, locality, property_type, property_subtype],
        outputs=out
    )

demo.launch()
