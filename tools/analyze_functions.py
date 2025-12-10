#!/usr/bin/env python3
# analyze_functions.py
# Analysiert data/devices/functions und dist/data/devices/functions
# Ausgabe: pro Datei: Typ, Kategorien, devices total, missing(MISSING__), real values count, beispiele
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "data" / "devices" / "functions"
DIST_DIR = ROOT / "dist" / "data" / "devices" / "functions"

def analyze_file(p):
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"file": str(p), "error": f"JSON parse error: {e}"}
    info = {"file": str(p)}
    info["type"] = type(doc).__name__
    # if top-level is list of categories with .devices
    if isinstance(doc, list):
        info["categories"] = len(doc)
        total = 0
        missing = 0
        real = 0
        examples_real = []
        examples_missing = []
        for cat in doc:
            devs = cat.get("devices") if isinstance(cat, dict) else None
            if isinstance(devs, list):
                total += len(devs)
                for d in devs:
                    v = d.get("value") if isinstance(d, dict) else None
                    if isinstance(v, str) and v.startswith("MISSING__"):
                        missing += 1
                        if len(examples_missing) < 6:
                            examples_missing.append({"category": cat.get("category"), "name": d.get("name"), "value": v})
                    elif v is None or (isinstance(v,str) and v.strip()==""):
                        missing += 1
                        if len(examples_missing) < 6:
                            examples_missing.append({"category": cat.get("category"), "name": d.get("name"), "value": v})
                    else:
                        real += 1
                        if len(examples_real) < 6:
                            examples_real.append({"category": cat.get("category"), "name": d.get("name"), "value": v})
        info.update({"total_devices": total, "missing": missing, "real": real,
                     "examples_real": examples_real, "examples_missing": examples_missing})
    elif isinstance(doc, dict):
        # print top-level keys and try to find any devices arrays inside
        info["keys"] = list(doc.keys())
        total = missing = real = 0
        examples_real = []
        examples_missing = []
        # search recursively for "devices" lists
        def walk(o):
            nonlocal total, missing, real, examples_real, examples_missing
            if isinstance(o, dict):
                for k,v in o.items():
                    if k=="devices" and isinstance(v, list):
                        for d in v:
                            if isinstance(d, dict):
                                total += 1
                                vv = d.get("value")
                                if isinstance(vv,str) and vv.startswith("MISSING__"):
                                    missing += 1
                                    if len(examples_missing) < 6:
                                        examples_missing.append({"name": d.get("name"), "value": vv})
                                elif vv is None or (isinstance(vv,str) and vv.strip()==""):
                                    missing += 1
                                    if len(examples_missing) < 6:
                                        examples_missing.append({"name": d.get("name"), "value": vv})
                                else:
                                    real += 1
                                    if len(examples_real) < 6:
                                        examples_real.append({"name": d.get("name"), "value": vv})
                    else:
                        walk(v)
            elif isinstance(o, list):
                for e in o:
                    walk(e)
        walk(doc)
        info.update({"total_devices": total, "missing": missing, "real": real,
                     "examples_real": examples_real, "examples_missing": examples_missing})
    else:
        info["note"] = "unexpected top-level JSON type"
    return info

def print_info(i):
    if i.get("error"):
        print(i["file"], "ERROR:", i["error"])
        return
    print("File:", i["file"])
    print("  type:", i.get("type"), " categories:", i.get("categories", '-'), " keys:", i.get("keys", '-'))
    print("  devices total:", i.get("total_devices",0), " real:", i.get("real",0), " missing:", i.get("missing",0))
    if i.get("examples_real"):
        print("  examples real (up to 5):")
        for ex in i["examples_real"]:
            print("    -", ex)
    if i.get("examples_missing"):
        print("  examples missing (up to 5):")
        for ex in i["examples_missing"]:
            print("    -", ex)
    print()

def main():
    print("Analyzing source files in:", SRC_DIR)
    for p in sorted(SRC_DIR.glob("*.json")):
        print_info(analyze_file(p))
    print("Analyzing dist files in:", DIST_DIR)
    if DIST_DIR.exists():
        for p in sorted(DIST_DIR.glob("*.json")):
            print_info(analyze_file(p))
    else:
        print("  dist dir not found:", DIST_DIR)
if __name__ == '__main__':
    main()
