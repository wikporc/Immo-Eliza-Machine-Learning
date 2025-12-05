# Immo-Eliza-Machine-Learning — README



## Table of Contents
- [Project purpose](#project-purpose)
- [Repository structure (key files & notebooks)](#repository-structure-key-files--notebooks)
  - [Data preparation](#data-preparation)
  - [Optimisation](#optimisation)
  - [Extracting params & raw features](#extracting-params--raw-features)
  - [Optimum training](#optimum-training)
  - [API & UI](#api--ui)
  - [Models & outputs](#models--outputs)
  - [Utilities & scripts](#utilities--scripts)
  - [Misc files](#misc-files)
- [Quick usage](#quick-usage)
- [How to reproduce model optimisation & extract params](#how-to-reproduce-model-optimisation--extract-params)
- [Notes & pointers](#notes--pointers)
- [Potential future improvements](#potential-future-improvements)

---

## Intro

My background is in Materials Science, but currently I am following a 7-month bootcamp in AI & Data Science with Becode(https://becode.org/). The goal of the project is to create a ML tool capable of predicting real-estate prices in Belgium.

The project is split into 4 phases:

- Week 1: Scraping the data (https://github.com/BogJ674/immo-eliza-scraping) - Team project
- Week 2: Exploratory Data Analysis (https://github.com/AmineSam/immo-eliza-gold-fishes-analysis) - Team project
- Week 3: ML training - Solo project
- Week 4: ML deployment - Solo project

Because of external factors, I was not present during the week 3. This repository contains both the training and deployment. Because of the time limitations, I had to cut some corners in order to submit a minimal viable product.
The data cleaning was taken from the EDA phase from week 2. A number of datasets were generated and a train/test split was performed:
- Global (Data only cleaned, preprocessed and split) 
- Luxury cluster (despite being called luxury, this cluster contains also properties such as an entire building complex with 1000s of apartments)
- Residential cluster (only "regular" houses and apartments)
- Only Houses
- Only Apartments


As well as double splits:
- Luxury cluster (only apartments)
- Luxury cluster (only houses)
- Residential cluster (only apartments)
- Residential cluster (only houses)

I used KMeans to separate the clusters. 
After some initial training, it was visible that trying to achieve a good modelling for the full dataset was not the way to go. Same goes for the luxury properties. 
In real-life situation, buying an entire complex is an entirely different situation that would require getting a manual quotation, or a separate modelling. Given the limited timeline, I did not do any further investigation on those properties, and instead I focused on getting good models for residential properties, with separate models for apartments and houses.

I used Gradio to create a simple UI capable of getting the input from the user, sending a request to the API and getting back a predicted price. It is quite simplified as it's a working prototype. I will probably redesign it to a Streamlit-based solution in the future, after some backend changes.

The backend is also simplified and lacks a lot of functions. I will expand them in the future before dockerisation.



---

## Repository structure (key files & notebooks)

### Data preparation
- [data_preparation.ipynb](data_preparation.ipynb) — Data cleaning, feature engineering and training helpers. Key symbols:
  - [`choose_params`](data_preparation.ipynb) — default model parameters selector.
  - [`build_preprocessor`](data_preparation.ipynb) — ColumnTransformer + Pipelines used for training.
  - [`train_all_models`](data_preparation.ipynb) — wrapper to train models on dataset splits.
  - [`complete_split`](data_preparation.ipynb), [`split_by_type`](data_preparation.ipynb) — dataset splitting helpers.
  - Notes in the notebook: configuration of categorical mappings (`state_grouped_mapping`, `kitchen_equipped_mapping`, `glazing_mapping`, `heating_mapping`) and columns dropped / kept during cleaning.

### Optimisation
- [optimisation.ipynb](optimisation.ipynb) — Optuna-driven hyperparameter search and autosave logic. Key symbols:
  - [`objective_xgb`](optimisation.ipynb), [`objective_lgbm`](optimisation.ipynb), [`objective_cat`](optimisation.ipynb) — per-model optimisation objectives (they build the pipeline, fit model, compute RMSE and autosave best).
  - [`tune_xgb`](optimisation.ipynb), [`tune_lgbm`](optimisation.ipynb), [`tune_catboost`](optimisation.ipynb) — tuning loops that persist best models into [models_optimisation/](models_optimisation/).
  - Preprocessor builder: [`build_preprocessor`](optimisation.ipynb) (same pattern as in data_preparation notebook).

### Extracting params & raw features
- [extract_best_parameters.ipynb](extract_best_parameters.ipynb) — Loads optuna-saved BEST model pickles and writes cleaned best-parameter JSON files for reuse (examples: XGBoost/LGBM/CatBoost extractions). See code that extracts `PARAM_KEYS` and writes JSONs under `models_optimisation/best_parameters/`.
- [raw_features_extractor.ipynb](raw_features_extractor.ipynb) — Extracts raw model input features from saved preprocessing pipelines and writes JSONs to [models_optimisation/raw_features/]. This produces `raw_features_apt.json` and `raw_features_house.json`.

### Optimum training
- [optimum_training.ipynb](optimum_training.ipynb) — Re-train final models using extracted best params & full training data (notebook contains training loop to create final saved pipelines).

### API & UI
- [api/app.py](api/app.py) — Gradio UI that prepares payloads and calls the prediction backend.
  - [`prepare_payload`](api/app.py) — builds the JSON payload sent to backend.
  - [`predict_api`](api/app.py) — calls the backend and formats the response.
  - UI logic: hierarchical locality selection using [locality_resolved_map_clean.json](locality_resolved_map_clean.json) → `regions` construction, dropdown update helpers: `update_provinces`, `update_municipalities`.
- [api/backend.py](api/backend.py) — FastAPI application exposing endpoints.
  - [`PropertyInput`](api/backend.py) — request Pydantic schema for `/predict`.
  - `GET /` healthcheck → [`alive`](api/backend.py).
  - `POST /predict` → [`make_prediction`](api/backend.py) which calls the server-side predict flow.
- [api/predict.py](api/predict.py) — Server-side prediction utilities.
  - [`load_feature_list`](api/predict.py), [`load_model`](api/predict.py) — loaders for features & models.
  - [`validate_input`](api/predict.py), [`preprocess_input`](api/predict.py), [`run_model`](api/predict.py), [`predict`](api/predict.py) — main preprocessing & prediction flow used by the API.
  - Feature / model assets referenced:
    - `models_optimisation/raw_features/raw_features_apt.json`
    - `models_optimisation/raw_features/raw_features_house.json`
    - Saved model pickles: e.g. `models_optimisation/cat_res_apt_BEST.pkl`, `models_optimisation/cat_res_house_BEST.pkl`

### Models & outputs
- [models_optimisation/](models_optimisation/) — optuna autosaved BEST models, best-parameters JSON files and raw features saved by the pipeline extraction notebooks.
- [models_before_optimisation/](models_before_optimisation/) — earlier baseline models.
- [datasets/](datasets/) — CSV splits produced by notebooks (train/test per cluster/type).
- [results_all_models_before_optimisation.csv](results_all_models_before_optimisation.csv) — benchmarking results.

### Utilities & scripts
- [generate_belgium_postal_map.py](generate_belgium_postal_map.py) — script to build postal/locality mapping used by the UI.
- [drop_unknowns.py](drop_unknowns.py) — helper script (data cleaning) that creates [locality_resolved_map_clean.json](locality_resolved_map_clean.json) from [locality_resolved_map.json](locality_resolved_map.json).

### Misc files
- [locality_resolved_map.json](locality_resolved_map.json) and [locality_resolved_map_clean.json](locality_resolved_map_clean.json)
- [requirements.txt](requirements.txt)
- [.gitignore](.gitignore)
- [README.md](README.md) — this file.

---

## Quick usage
- Install deps:
```bash
pip install -r requirements.txt
```
- Run FastAPI backend (serves /predict):
```bash
uvicorn api.backend:api --reload --port 8010
```
- Run Gradio UI frontend (starts local UI and calls the backend):
```bash
python api/app.py
```

---

## How to reproduce model optimisation & extract params
1. Prepare datasets using [data_preparation.ipynb](data_preparation.ipynb) (see [`choose_params`](data_preparation.ipynb), [`build_preprocessor`](data_preparation.ipynb)).
2. Run optuna optimisation in [optimisation.ipynb](optimisation.ipynb) which saves best pickles to [models_optimisation/](models_optimisation/) (see [`tune_xgb`](optimisation.ipynb), [`tune_lgbm`](optimisation.ipynb), [`tune_catboost`](optimisation.ipynb)).
3. Run [extract_best_parameters.ipynb](extract_best_parameters.ipynb) to write best params JSONs for each model type.
4. Use [raw_features_extractor.ipynb](raw_features_extractor.ipynb) to generate raw feature JSONs consumed by the API.
5. Optionally re-train final models in [optimum_training.ipynb](optimum_training.ipynb).

---

## Notes & pointers
- The API prediction flow is implemented in [api/predict.py](api/predict.py): input validation (`[`validate_input`](api/predict.py)`), preprocessing (`[`preprocess_input`](api/predict.py)`), and prediction (`[`run_model`](api/predict.py)`).
- Gradio UI uses the locality mapping file [locality_resolved_map_clean.json](locality_resolved_map_clean.json) and the mapping code inside [api/app.py](api/app.py) (`update_provinces`, `update_municipalities`).
- Saved best-model pickles live in [models_optimisation/](models_optimisation/) and are loaded by the API via [`load_model`](api/predict.py).

---


## Known bugs:

- At the moment, the user has to enter the Advanced features tab and press "Save Advanced Inputs", even when they have no intention to provide any advanced inputs. Only when both basic and advanced inputs are saved, the "Predict price" button will result in a price being printed (otherwise no price appears)

## Potential future expansions:

### Expand the backend:
- Improve locality resolution: fallback heuristics or fuzzy matching for unseen municipality/locality entries. Currently, the hierarchy of Region->Province->Municipality is handled in the frontend. 
- Dockerise the API
- Add authentication and rate-limiting to the API (API key or OAuth).
- Give information on the price range instead of just a simple number
- Add telemetry / monitoring (Prometheus + Grafana) and structured logging.
- Implement a DL solution combining tabular data and images of properties.
- Add information about prices in neighbouring municipalities
- Add authentication and rate-limiting to the API (API key or OAuth)

### UI:
- Fix the advanced inputs bug.
- Rewrite the UI into a Streamlit-based solution that looks more professional than the current simple prototype.
- Deploy the UI

### Others:
- Convert the notebooks into scripts and clean unnecessary duplicating clutter
