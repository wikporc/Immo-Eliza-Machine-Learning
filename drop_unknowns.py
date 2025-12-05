import json

INPUT_JSON = r"locality_resolved_map.json"  
OUTPUT_JSON = "locality_resolved_map_clean.json"

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

clean = {}
dropped = 0

for loc, info in data.items():
    muni = info.get("municipality", "")
    prov = info.get("province", "")
    reg  = info.get("region", "")

    
    # if muni == "UNKNOWN":

   
    if "UNKNOWN" in {muni, prov, reg}:
        dropped += 1
        continue

    clean[loc] = info

print(f"Total entries in input : {len(data)}")
print(f"Dropped (with UNKNOWN): {dropped}")
print(f"Kept                  : {len(clean)}")

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(clean, f, ensure_ascii=False, indent=2)

print(f"Saved cleaned map to: {OUTPUT_JSON}")
