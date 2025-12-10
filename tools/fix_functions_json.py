#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_functions_json.py
Normalisiert / repariert JSONs in data/devices/functions:
 - stellt sicher, dass jede Kategorie ein "devices" array hat
 - stellt sicher, dass jedes device ein dict mit keys name,type,value ist
 - konvertiert strings/arrays in dicts
 - setzt fehlende/leer value -> "MISSING__<Kategorie>_<Name>"
 - legt Backup *.bak an
"""
import json, os, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEV_DIR = ROOT / "data" / "devices" / "functions"

def safe_name(s):
    if not s:
        return "unnamed"
    return re.sub(r'[^A-Za-z0-9]+', '_', str(s)).strip('_')

def normalize_device(dev, category):
    # returns normalized device dict and a flag whether changed
    changed = False
    # If device is string -> use as name
    if isinstance(dev, str):
        name = dev
        devn = {"name": name, "type": "switch", "value": None}
        return devn, True
    # If device is list/tuple -> stringify elements to name
    if isinstance(dev, (list, tuple)):
        name = " ".join([str(x) for x in dev if x is not None])
        devn = {"name": name or "item", "type": "switch", "value": None}
        return devn, True
    # If already a dict
    if isinstance(dev, dict):
        d = dict(dev)  # copy
        # ensure keys
        if "name" not in d or not d.get("name"):
            # attempt to infer from 'value' or other keys
            if isinstance(d.get("value"), str) and "." in d.get("value"):
                d["name"] = d.get("value").split(".")[-1]
            else:
                d["name"] = d.get("label") or d.get("title") or d.get("id") or "unnamed"
            changed = True
        if "type" not in d or not d.get("type"):
            # infer
            vt = d.get("value")
            if isinstance(vt, str) and (vt.lower().find("screen")>=0 or vt.lower().find("fullybrowser")>=0):
                d["type"] = "link"
            else:
                d["type"] = "switch"
            changed = True
        # If value is non-primitive (dict/list), stringify attempt and set to None
        v = d.get("value", None)
        if isinstance(v, (dict, list)):
            # if dict has 'state' key, try that
            if isinstance(v, dict) and "state" in v and isinstance(v["state"], str):
                d["value"] = v["state"]
            else:
                # drop complex value - will put placeholder below
                d["value"] = None
            changed = True
        # ensure name is string
        d["name"] = str(d.get("name"))
        return d, changed
    # fallback: stringify whatever it is
    return {"name": str(dev), "type": "switch", "value": None}, True

def process_file(path: Path):
    changed_any = False
    placeholders = []
    examples = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"file": str(path), "error": f"JSON parse error: {e}"}

    if not isinstance(data, list):
        return {"file": str(path), "error": "expected top-level array of categories"}

    for cat in data:
        if not isinstance(cat, dict):
            continue
        cat_name = cat.get("category") or "Allgemein"
        # ensure devices list
        devs = cat.get("devices")
        if not isinstance(devs, list):
            cat["devices"] = []
            devs = cat["devices"]
            changed_any = True
        new_devs = []
        for dev in devs:
            devn, changed = normalize_device(dev, cat_name)
            # if value missing/empty -> set placeholder
            v = devn.get("value")
            if v is None or (isinstance(v, str) and v.strip() == ""):
                placeholder = f"MISSING__{safe_name(cat_name)}_{safe_name(devn.get('name'))}"
                devn["value"] = placeholder
                placeholders.append({"file": str(path), "category": cat_name, "name": devn.get("name"), "placeholder": placeholder})
                changed_any = True
            new_devs.append(devn)
            if changed:
                changed_any = True
                if len(examples) < 6:
                    examples.append({"category": cat_name, "before": dev, "after": devn})
        cat["devices"] = new_devs

    if changed_any:
        # write backup and new file
        bak = path.with_suffix(path.suffix + ".bak")
        path.rename(bak)  # move original to .bak
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"file": str(path), "fixed": True, "placeholders": len(placeholders), "examples": examples}
    else:
        return {"file": str(path), "fixed": False, "placeholders": 0}

def main():
    results = []
    for p in sorted(DEV_DIR.glob("*.json")):
        res = process_file(p)
        results.append(res)
    # summary print
    total_fixed = sum(1 for r in results if r.get("fixed"))
    total_placeholders = sum(r.get("placeholders",0) for r in results)
    print("Processed files:", len(results))
    print("Files changed:", total_fixed)
    print("Placeholders added:", total_placeholders)
    for r in results:
        if r.get("error"):
            print("ERROR:", r["file"], r["error"])
        elif r.get("fixed"):
            print("FIXED:", r["file"], "-", r.get("placeholders",0), "placeholders; examples:")
            for ex in r.get("examples",[]):
                print("   example:", ex)
    print("Backups for changed files saved with suffix .bak in same folder.")
    print("Done.")

if __name__ == '__main__':
    main()
