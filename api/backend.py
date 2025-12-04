from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Literal
from .predict import predict


api = FastAPI(
    title="Immo Eliza Price API",
    version="1.0.0"
)

# ===============================
# REQUEST SCHEMA
# ===============================

class PropertyInput(BaseModel):
    # Required
    rooms: float
    area: float
    locality: str
    property_type: Literal["apartment", "house"]
    property_subtype: str

    # Optional
    state: Optional[float] = None
    facades_number: Optional[float] = None
    is_furnished: Optional[float] = None
    has_terrace: Optional[float] = None
    has_garden: Optional[float] = None
    has_swimming_pool: Optional[float] = None
    has_equipped_kitchen: Optional[float] = None
    build_year: Optional[float] = None
    cellar: Optional[float] = None
    garage: Optional[float] = None
    bathrooms: Optional[float] = None
    heating_type: Optional[float] = None
    terrace_surface: Optional[float] = None
    sewer_connection: Optional[float] = None
    running_water: Optional[float] = None
    primary_energy_consumption: Optional[float] = None
    co2: Optional[float] = None
    certification_electrical_installation: Optional[float] = None
    preemption_right: Optional[float] = None
    flooding_area_type: Optional[float] = None
    leased: Optional[float] = None
    living_room_surface: Optional[float] = None
    glazing_type: Optional[float] = None
    elevator: Optional[float] = None
    entry_phone: Optional[float] = None
    access_disabled: Optional[float] = None
    apartement_floor: Optional[float] = None
    number_floors: Optional[float] = None
    toilets: Optional[float] = None


# ===============================
# ROUTES
# ===============================

@api.get("/")
def alive():
    return {"status": "alive"}

@api.post("/predict")
def make_prediction(item: PropertyInput):
    data = item.dict()
    result = predict(data)
    return result
