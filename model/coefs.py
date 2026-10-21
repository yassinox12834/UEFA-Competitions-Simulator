from uefa.config import COEFS_JSON
import json

coefs = {
    "UCL": {
        "Qualifying":     {"comp_mult": 3.0, "stage_mult": 0.8},
        "League":         {"comp_mult": 3.0, "stage_mult": 1.0},
        "Playoff":        {"comp_mult": 3.0, "stage_mult": 1.1},
        "Round of 16":    {"comp_mult": 3.0, "stage_mult": 1.2},
        "Quarter Final":  {"comp_mult": 3.0, "stage_mult": 1.3},
        "Semi Final":     {"comp_mult": 3.0, "stage_mult": 1.4},
        "Final":          {"comp_mult": 3.0, "stage_mult": 1.5},
    },
    "UEL": {
        "Qualifying":     {"comp_mult": 2.0, "stage_mult": 0.8},
        "League":         {"comp_mult": 2.0, "stage_mult": 1.0},
        "Playoff":        {"comp_mult": 2.0, "stage_mult": 1.1},
        "Round of 16":    {"comp_mult": 2.0, "stage_mult": 1.2},
        "Quarter Final":  {"comp_mult": 2.0, "stage_mult": 1.3},
        "Semi Final":     {"comp_mult": 2.0, "stage_mult": 1.4},
        "Final":          {"comp_mult": 2.0, "stage_mult": 1.5},
    },
    "UECL": {
        "Qualifying":     {"comp_mult": 1.5, "stage_mult": 0.8},
        "League":         {"comp_mult": 1.5, "stage_mult": 1.0},
        "Playoff":        {"comp_mult": 1.5, "stage_mult": 1.1},
        "Round of 16":    {"comp_mult": 1.5, "stage_mult": 1.2},
        "Quarter Final":  {"comp_mult": 1.5, "stage_mult": 1.3},
        "Semi Final":     {"comp_mult": 1.5, "stage_mult": 1.4},
        "Final":          {"comp_mult": 1.5, "stage_mult": 1.5},
    },
    "Domestic Cup": {
        "Early Rounds":   {"comp_mult": 0.5, "stage_mult": 0.9},
        "Round of 32":    {"comp_mult": 0.5, "stage_mult": 1.0},
        "Round of 16":    {"comp_mult": 0.5, "stage_mult": 1.1},
        "Quarter Final":  {"comp_mult": 0.5, "stage_mult": 1.2},
        "Semi Final":     {"comp_mult": 0.5, "stage_mult": 1.3},
        "Final":          {"comp_mult": 0.5, "stage_mult": 1.5},
    },
    "League": {
        "comp_mult": 1.0,
        "stage_mult": 1.0
    },
    "Domestic Super Cup": {
        "comp_mult": 0.8,
        "stage_mult": 1.0
    },
    "UEFA Super Cup": {
        "comp_mult": 2.5,
        "stage_mult": 1.0
    }
}

# Helper: get K for any competition (and stage, if nested)
def get_k(coefs, competition, stage=None, k_base=16):
    entry = coefs[competition]
    if stage is not None:
        entry = entry[stage]
    return k_base * entry["comp_mult"] * entry["stage_mult"]

# Sanity checks
print("UCL Final:", get_k(coefs, "UCL", "Final"))
print("League:", get_k(coefs, "League"))
print("Domestic Cup Final:", get_k(coefs, "Domestic Cup", "Final"))
print("UEFA Super Cup:", get_k(coefs, "UEFA Super Cup"))

with open(COEFS_JSON, "w") as f:
    json.dump(coefs, f, indent=2)

print("\nSaved to coefs.json")