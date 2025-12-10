#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_functions_from_minuvis.py (robust)
Liest ein MinuVis / Mobile JSON export (z.B. 0_userdata.0_minukodu_Mobile.json)
und generiert:
 - data/main/functions.json
 - data/devices/functions/<slugified_page>.json

Verbesserungen:
 - slugifiziert Dateinamen (keine '/' mehr, Umlaute werden behandelt)
 - legt Zielverzeichnisse rekursiv an
"""
import json
import os
import sys
import unicodedata
import re

# --- CONFIG ---
DASHBOARD_ROOT = os.path.abspath(os.path.dirname(__file__) + "/..")  # expects script in tools/
TARGET_PAGES = ["Licht", "Ambiente", "Schalter", "Türen/Fenster", "Aktiv", "Dashboards"]
OUT_MAIN = os.path.join(DASHBOARD_ROOT, "data", "main", "functions.json")
OUT_DEV_DIR = os.path.join(DASHBOARD_ROOT, "data", "devices", "functions")
AUTH_USERS = ["admin", "bernd", "isa", "gast"]  # deine user-IDs

# --- Helpers ---
def safe_mkdir(path):
    os.makedirs(path, exist_ok=True)

def slugify(text):
    if not text:
        return "page"
    # replace German umlauts first for readable filenames
    text = text.replace('ä','ae').replace('ö','oe').replace('ü','ue').replace('Ä','Ae').replace('Ö','Oe').replace('Ü','Ue').replace('ß','ss')
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii','ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    text = text.strip('_')
    return text or "page"

def load_minivis(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_categories(page):
    """
    Page is the MinuVis page dict.
    Rule:
      - headline widgets start a new category
      - following widgets of interesting types (switch, indicator, linkbutton, html, output)
        are appended as devices to current category
    """
    widgets = page.get("widgets", [])
    cats = []
    cur = None
    for w in widgets:
        t = w.get("type")
        # Treat variants/capitalization
        tt = (t or "").lower()
        if tt == "headline":
            txt = (w.get("title") or w.get("text") or w.get("label") or w.get("name") or "").strip()
            if not txt:
                txt = "Unnamed"
            cur = {"category": txt, "devices": []}
            cats.append(cur)
        elif tt in ("switch", "output", "indicator", "html", "linkbutton", "button"):
            # pick best state/target info
            stateId = w.get("stateId") or w.get("dataSource") or w.get("link") or w.get("targetpage") or w.get("extUrl") or w.get("target") or None
            name = w.get("title") or w.get("label") or w.get("name") or w.get("text") or None
            if not name:
                if isinstance(stateId, str):
                    name = stateId.split(".")[-1]
                else:
                    name = tt
            # map to our schema types
            if tt == "switch":
                dtype = "switch"
            elif tt == "indicator":
                dtype = "indicator"
            elif tt in ("linkbutton","button"):
                dtype = "link"
            elif tt == "html":
                dtype = "html"
            else:
                dtype = "switch"
            dev = {"name": name, "type": dtype, "value": stateId}
            if cur is None:
                cur = {"category": "Allgemein", "devices": [dev]}
                cats.append(cur)
            else:
                cur["devices"].append(dev)
        else:
            # ignore other widget types by default
            continue
    return cats

def page_by_title(pages, title):
    for p in pages:
        if p.get("title") == title:
            return p
    return None

def main(minuvis_json):
    print("MinuVis file:", minuvis_json)
    mv = load_minivis(minuvis_json)
    pages = mv.get("pages", [])
    pages_map = {p.get("title"): p for p in pages}

    safe_mkdir(OUT_DEV_DIR)

    functions_main = {
        "name": "Funktionen",
        "type": "functions",
        "icon": "fa-cogs",
        "authorization": AUTH_USERS,
        "content": [
            {
                "category": "",
                "tiles": []
            }
        ]
    }

    for title in TARGET_PAGES:
        p = page_by_title(pages, title)
        if not p:
            print("WARN: Seite nicht gefunden in MinuVis:", title)
            continue
        slug = slugify(title)
        fname = slug + ".json"
        outpath = os.path.join(OUT_DEV_DIR, fname)
        # ensure directory exists
        safe_mkdir(os.path.dirname(outpath))
        cats = extract_categories(p)
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(cats, f, indent=2, ensure_ascii=False)
        print(" -> geschrieben:", outpath, " (categories:", len(cats), ")")
        # add tile entry
        functions_main["content"][0]["tiles"].append({
            "name": title,
            "json": fname,
            "image": slug + ".webp",
            "status": []
        })

    # write main functions.json
    safe_mkdir(os.path.dirname(OUT_MAIN))
    with open(OUT_MAIN, "w", encoding="utf-8") as f:
        json.dump(functions_main, f, indent=2, ensure_ascii=False)
    print("Hauptdatei geschrieben:", OUT_MAIN)
    print("Fertig. Bitte npx gulp ausführen und Service neu starten.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: {} /pfad/zu/0_userdata.0_minukodu_Mobile.json".format(sys.argv[0]))
        sys.exit(1)
    minuvis_json = sys.argv[1]
    main(minuvis_json)
