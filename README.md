

# Immo-Eliza-Machine-Learning — README

Project purpose
- Pipeline to prepare Belgian real-estate data, train/optimise price-prediction models (XGBoost / LightGBM / CatBoost), extract best hyperparameters and expose a small API + Gradio UI for predictions.

Repository structure (key files & notebooks)
- data_preparation.ipynb — Data cleaning, feature engineering and training helpers. Key symbols:
  - `choose_params` — default model parameters selector.
  - `build_preprocessor` — ColumnTransformer + Pipelines used for training.
  - `train_all_models` — wrapper to train models on dataset splits.
  - `complete_split`, `split_by_type` — dataset splitting helpers.
- optimisation.ipynb — Optuna-driven hyperparameter search and autosave logic. Key symbols:
  - `objective_xgb`, `objective_lgbm`, `objective_cat` — per-model optimisation objectives.
  - `tune_xgb`, `tune_lgbm`, `tune_catboost` — tuning loops that persist best models.
- extract_best_parameters.ipynb — Loads optuna-saved BEST model pickles and writes cleaned best-parameter JSON files for reuse.
- raw_features_extractor.ipynb — Extracts raw model input features from saved preprocessing pipelines and writes JSONs to raw_features.
- optimum_training.ipynb — (notebooks used to re-train final optimum models; see notebook for details).
- app.py — Gradio UI that prepares payloads and calls the prediction backend. Key symbols:
  - `prepare_payload` — builds the JSON payload sent to backend.
  - `predict_api` — calls the backend and formats the response.
- backend.py — FastAPI application exposing endpoints. Key symbols:
  - `PropertyInput` — request Pydantic schema.
  - `make_prediction` — POST /predict route.
  - `alive` — healthcheck GET /.
- predict.py — Server-side prediction utilities. Key symbols:
  - [`load_feature_list`](api/predict.py), [`load_model`](api/predict.py) — loaders for features & models.
  - [`validate_input`](api/predict.py), [`preprocess_input`](api/predict.py), [`run_model`](api/predict.py), [`predict`](api/predict.py) — main preprocessing & prediction flow used by the API.
- Models & outputs
  - models_optimisation — optuna autosaved BEST models, best-parameters JSON files and raw features saved by the pipeline extraction notebooks.
  - models_before_optimisation — earlier models (baseline).
  - datasets — CSV splits produced by notebooks (train/test per cluster/type).
  - results_all_models_before_optimisation.csv — benchmarking results.
- Utilities & scripts
  - generate_belgium_postal_map.py — script to build postal/locality mapping used by the UI.
  - drop_unknowns.py — helper script (data cleaning).
- Misc
  - locality_resolved_map.json and locality_resolved_map_clean.json — locality → region/province/municipality map used by the UI.
  - requirements.txt — Python deps.
  - .gitignore
  - README.md — this file.

Quick usage
- Install deps:
  ```bash
  pip install -r requirements.txt
  ```
- Run FastAPI backend (serves /predict):
  ```bash
  uvicorn api.backend:api --reload --port 8010
  ```
  - backend implementation: `api.backend:api`
- Run Gradio UI frontend (starts local UI and calls the backend):
  ```bash
  python api/app.py
  ```
  - UI implementation: app.py — uses [`prepare_payload`](api/app.py) and [`predict_api`](api/app.py).

How to reproduce model optimisation & extract params
1. Prepare datasets using data_preparation.ipynb (see [`choose_params`](data_preparation.ipynb], `build_preprocessor`).
2. Run optuna optimisation in optimisation.ipynb which saves best pickles to models_optimisation (see `tune_xgb`, `tune_lgbm`, `tune_catboost`).
3. Run extract_best_parameters.ipynb to write best params JSONs for each model type.
4. Use raw_features_extractor.ipynb to generate raw feature JSONs consumed by the API.

Notes & pointers
- The API prediction flow is implemented in predict.py: input validation (`[`validate_input`](api/predict.py)`), preprocessing (`[`preprocess_input`](api/predict.py)`), and prediction (`[`run_model`](api/predict.py)`).
- Gradio UI uses the locality mapping file locality_resolved_map_clean.json and mapping code inside app.py.
- Saved best-model pickles live in models_optimisation and are loaded by the API via `load_model`.

