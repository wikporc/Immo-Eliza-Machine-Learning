import pandas as pd
import json
import numpy as np

# ======================================================
# 1) INPUT FILES
# ======================================================

DF_DATASET = r"datasets\cleaned_dataset_v4.csv"
DF_ZIPCODES = r"api\zipcodes_num_nl_2025.xls"

# ======================================================
# 2) LOAD DATA
# ======================================================

df = pd.read_csv(DF_DATASET)
df_zip = pd.read_excel(DF_ZIPCODES)

# normalize column names
df.columns = [c.lower() for c in df.columns]
df_zip.columns = [c.lower() for c in df_zip.columns]

# identify important columns
locality_col = "locality"
postal_col_candidates = ["postal_code", "postcode", "zipcode"]
zip_col = next(c for c in postal_col_candidates if c in df_zip.columns)

city_col_candidates = ["hoofdgemeente", "city", "municipality"]
city_col = next(c for c in city_col_candidates if c in df_zip.columns)

prov_col_candidates = ["province", "provincie"]
prov_col = next(c for c in prov_col_candidates if c in df_zip.columns)

region_col_candidates = ["region", "gewest"]
region_col = next((c for c in region_col_candidates if c in df_zip.columns), None)

# normalize zipcodes to string
df[postal_col_candidates[0]] = df[postal_col_candidates[0]].astype(str).str.strip()
df_zip[zip_col] = df_zip[zip_col].astype(str).str.strip()

# ======================================================
# 3) FIXED MAPPING: PROVINCE → REGION (if missing)
# ======================================================

province_to_region = {
    # Flanders
    "antwerpen": "Flanders",
    "oost-vlaanderen": "Flanders",
    "west-vlaanderen": "Flanders",
    "vlaams-brabant": "Flanders",
    "limburg": "Flanders",

    # Wallonia
    "hainaut": "Wallonia",
    "henegouwen": "Wallonia",
    "liège": "Wallonia",
    "luik": "Wallonia",
    "luxembourg": "Wallonia",
    "namur": "Wallonia",
    "brabant wallon": "Wallonia",
    "waals-brabant": "Wallonia",

    # Brussels
    "brussels": "Brussels",
    "brussel": "Brussels",
    "bruxelles": "Brussels",
}

# normalize province names in ZIP file
df_zip["province_norm"] = df_zip[prov_col].str.lower().str.strip()

if region_col:
    df_zip["region"] = df_zip[region_col]
else:
    df_zip["region"] = df_zip["province_norm"].map(province_to_region)

# Remove rows without region
df_zip = df_zip[df_zip["region"].notna()].copy()

# ======================================================
# 4) BUILD MAP: LOCALITY → MOST LIKELY MUNICIPALITY
# ======================================================

# Step A: extract postal codes used per locality in dataset
locality_map = {}

for loc, subdf in df.groupby(locality_col):
    loc = str(loc).strip().lower()
    if loc == "" or loc == "unknown":
        continue

    postals = subdf[postal_col_candidates[0]].dropna().astype(str)
    counts = postals.value_counts()

    if counts.empty:
        continue

    # choose postal code with highest frequency
    best_postal = counts.index[0]
    locality_map[loc] = {
        "postal_code": best_postal,
        "frequency": int(counts.iloc[0])
    }

# Step B: match postal codes to municipality/province/region
municipality_map = {}

for loc, info in locality_map.items():
    pcode = info["postal_code"]

    match = df_zip[df_zip[zip_col] == pcode]

    if match.empty:
        municipality_map[loc] = {
            "postal_code": pcode,
            "municipality": "UNKNOWN",
            "province": "UNKNOWN",
            "region": "UNKNOWN"
        }
        continue

    row = match.iloc[0]
    municipality_map[loc] = {
        "postal_code": pcode,
        "municipality": row[city_col],
        "province": row[prov_col],
        "region": row["region"]
    }

# Save locality resolution map
with open("locality_resolved_map.json", "w", encoding="utf-8") as f:
    json.dump(municipality_map, f, ensure_ascii=False, indent=2)

print("[OK] locality_resolved_map.json created")

# ======================================================
# 5) BUILD ADMIN STRUCTURE: Region → Province → Municipality
# ======================================================

admin = {}

for loc, info in municipality_map.items():
    region = info["region"]
    province = info["province"]
    city = info["municipality"]

    if "unknown" in {region.lower(), province.lower(), city.lower()}:
        continue

    admin.setdefault(region, {})
    admin[region].setdefault(province, set())
    admin[region][province].add(city)

# convert sets → sorted lists
for region in admin:
    for prov in admin[region]:
        admin[region][prov] = sorted(list(admin[region][prov]))

# save final structure
with open("belgium_admin_map.json", "w", encoding="utf-8") as f:
    json.dump(admin, f, ensure_ascii=False, indent=2)

print("[OK] belgium_admin_map.json created")
