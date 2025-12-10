#!/usr/bin/env python3
"""
Setzt sinnvolle device.type-Werte in data/devices/functions/*.json,
damit die Funktionen-Seiten (Licht, Ambiente, Schalter, Türen/Fenster usw.)
im Dashboard Geräte anzeigen.

Wird nur für Einträge mit echtem value (kein Platzhalter "xxx") aktiv.
Vor Änderungen wird jeweils eine Backup-Datei <name>.pretype angelegt.
"""

import json
import os
from pathlib import Path

BASE = Path("/opt/iobroker/iobroker-data/files/dashboard/data/devices/functions")

# Zuordnung: Dateiname (ohne .json) -> default type
TYPE_MAP = {
    "licht": "light",
    "ambiente": "light",
    "schalter": "plug",
    "tueren_fenster": "plug",

    # Die folgenden brauchst du erstmal nicht zwingend,
    # sind aber der Vollständigkeit halber gemappt:
    "dekorationslicht": "light",
    "fenster": "window",
    "gartengerate": "plug",
    "haushalt": "plug",
    "heizung": "heater",
    "unterhaltung": "media",
    "wetter": "temperature",

    # „aktiv“ und „dashboards“ behandeln wir (noch) als Buttons,
    # bis wir sie später sauber aufbauen.
    "aktiv": "button",
    "dashboards": "button",
}

def main():
    if not BASE.exists():
        print(f"Basis-Pfad {BASE} existiert nicht.")
        return

    processed = 0
    changed_files = 0

    for path in sorted(BASE.glob("*.json")):
        fname = path.name
        base = path.stem  # z.B. "licht"
        default_type = TYPE_MAP.get(base, "button")

        with path.open("r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"[WARN] {fname}: JSON-Fehler: {e}")
                continue

        if not isinstance(data, list):
            print(f"[WARN] {fname}: Unerwartete Struktur (erwarte Liste).")
            continue

        processed += 1
        changed = False
        devices_total = 0
        devices_typed = 0

        for cat in data:
            devices = cat.get("devices", [])
            if not isinstance(devices, list):
                continue

            for dev in devices:
                if not isinstance(dev, dict):
                    continue

                # nur echte Einträge, keine Dummy-"xxx"-Platzhalter
                value = dev.get("value")
                if not value or value == "xxx":
                    continue

                devices_total += 1
                if dev.get("type"):
                    devices_typed += 1
                    continue

                dev["type"] = default_type
                devices_typed += 1
                changed = True

        if changed:
            backup = path.with_suffix(path.suffix + ".pretype")
            if not backup.exists():
                path.replace(backup)
                # neu schreiben
                with path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                # falls Backup schon existiert, nur überschreiben
                with path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

            changed_files += 1
            print(f"[OK] {fname}: {devices_typed}/{devices_total} Devices mit type='{default_type}' versehen.")
        else:
            print(f"[OK] {fname}: nichts zu ändern (Devices mit type vorhanden oder nur Platzhalter).")

    print(f"\nFertig. Dateien verarbeitet: {processed}, geändert: {changed_files}")


if __name__ == "__main__":
    main()
