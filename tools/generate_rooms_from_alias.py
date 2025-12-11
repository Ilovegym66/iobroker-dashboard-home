#!/usr/bin/env python3
"""
generate_rooms_from_alias.py

Liest eine exportierte alias.0.Haus.json aus ioBroker und erzeugt daraus
eine data/main/rooms.json für das ioBroker Dashboard.

Aufruf:
    python3 tools/generate_rooms_from_alias.py /pfad/zu/alias.0.Haus.json
"""

import json
import sys
import re
import collections
from pathlib import Path


# Diese "Top-Level-Kategorien" aus alias.0.Haus werden ignoriert
IGNORE_TOP = {"Abfall", "Energie", "Netzwerk", "Notifications"}

# Reihenfolge der Ebenen im Dashboard
FLOOR_ORDER = {
    "Erdgeschoss": 10,
    "Obergeschoss": 20,
    "Dachgeschoss": 30,
    "Keller": 40,
    "Garage": 50,
    "Carport": 60,
    "Garten": 70,
    "Terrasse": 80,
    "Shop": 90,
}


def normalize_text(s: str) -> str:
    """Macht aus 'Arbeitszimmer_Bernd' -> 'Arbeitszimmer Bernd', inkl. ue->ü etc."""
    s = s.replace("_", " ")
    repl = [("ue", "ü"), ("ae", "ä"), ("oe", "ö")]
    for a, b in repl:
        s = re.sub(a, b, s, flags=re.IGNORECASE)
    return " ".join(w.capitalize() for w in s.split())


def slugify_room(floor: str, room: str) -> str:
    """Erzeugt einen Dateinamen-Slug für json-Feld (ohne .json)."""
    base = f"{floor}_{room}".lower()
    base = (base
            .replace("ä", "ae")
            .replace("ö", "oe")
            .replace("ü", "ue")
            .replace("ß", "ss"))
    base = base.replace(" ", "_").replace("-", "_")
    return base


def generate_rooms_from_alias(alias_json: Path, root: Path) -> Path:
    """Erzeugt rooms.json im data/main-Ordner. Gibt Pfad zur neuen Datei zurück."""
    if not alias_json.is_file():
        raise FileNotFoundError(f"Alias-Datei nicht gefunden: {alias_json}")

    with alias_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # alias.0.Haus.<Ebene>.<Raum>.*
    floor_rooms = collections.defaultdict(set)

    for key in data.keys():
        if not key.startswith("alias.0.Haus."):
            continue
        parts = key.split(".")
        if len(parts) < 5:
            continue
        floor = parts[3]
        room = parts[4]

        if floor in IGNORE_TOP:
            continue

        floor_rooms[floor].add(room)

    floors_sorted = sorted(
        floor_rooms.keys(),
        key=lambda f: FLOOR_ORDER.get(f, 1000)
    )

    # Verfügbare Raum-Bilder ermitteln (data/img/main/rooms/*.webp)
    rooms_img_dir = root / "data" / "img" / "main" / "rooms"
    available_imgs = []
    if rooms_img_dir.is_dir():
        available_imgs = [p.name for p in rooms_img_dir.glob("*.webp")]

    def find_image(room_name_nice: str) -> str:
        """Versucht, ein passendes Bild zu finden, sonst Fallback."""
        if not available_imgs:
            return "WohnEsszimmer.webp"

        key = room_name_nice.replace(" ", "").lower()
        candidates = [
            img for img in available_imgs
            if key in img.replace(".webp", "").lower()
        ]
        if candidates:
            return candidates[0]

        # Fallback: nur erstes Wort matchen
        first = room_name_nice.split()[0].lower()
        candidates = [
            img for img in available_imgs
            if first in img.replace(".webp", "").lower()
        ]
        if candidates:
            return candidates[0]

        return "WohnEsszimmer.webp"

    content = []

    for floor in floors_sorted:
        rooms = sorted(floor_rooms[floor])
        if not rooms:
            continue

        category_block = {
            "category": floor,
            "tiles": []
        }

        for room in rooms:
            room_nice = normalize_text(room)
            slug = slugify_room(floor, room)
            image = find_image(room_nice)

            tile = {
                "name": room_nice,
                "json": slug,        # -> erwartet data/devices/rooms/<slug>.json
                "image": image,      # z.B. Kueche.webp, WohnEsszimmer.webp, ...
                "status": []         # kannst du später manuell füllen
            }
            category_block["tiles"].append(tile)

        content.append(category_block)

    rooms_main = {
        "name": "Räume",
        "type": "rooms",
        "icon": "fa-door-open",
        "authorization": ["admin", "bernd", "isa", "gast"],
        "content": content
    }

    out_path = root / "data" / "main" / "rooms.json"

    # Backup der bestehenden rooms.json
    if out_path.exists():
        backup = out_path.with_suffix(".json.bak")
        backup.write_text(out_path.read_text(encoding="utf-8"),
                          encoding="utf-8")
        print(f"Backup der bestehenden rooms.json: {backup}")

    out_path.write_text(
        json.dumps(rooms_main, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"Neue rooms.json geschrieben nach: {out_path}")

    return out_path


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("Aufruf: python3 tools/generate_rooms_from_alias.py /pfad/zu/alias.0.Haus.json")
        sys.exit(1)

    alias_path = Path(argv[0]).expanduser().resolve()
    root = Path(__file__).resolve().parents[1]

    try:
        out_path = generate_rooms_from_alias(alias_path, root)
    except Exception as e:
        print(f"FEHLER: {e}")
        sys.exit(1)

    print("Fertig.")
    print("Hinweis: Für jede Kachel wird ein json-Slug erzeugt (json-Feld).")
    print("Lege unter data/devices/rooms/ passende <slug>.json Dateien an,")
    print("oder passe die json-Felder in data/main/rooms.json manuell an.")


if __name__ == "__main__":
    main()
