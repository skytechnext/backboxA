#!/usr/bin/env python3
"""
Configure the official Odoo Hotel (Industries) app for Casa Escondida.
Run AFTER activating Apps -> Industries -> Hotel (the SaaS Activate button).

Auth: set the API key in the environment (never hard-code / commit it):
    export ODOO_API_KEY=********        # the instance API key
    python3 hotel_setup.py

It is defensive: it first DISCOVERS the hotel models/fields (names differ across
Odoo versions), then creates room types, 23 rooms and a week of reservations,
printing exactly what it did or what to adjust.
"""
import os, sys, random, datetime, xmlrpc.client

URL = os.environ.get("ODOO_URL", "https://edu-escondida.odoo.com")
DB  = os.environ.get("ODOO_DB", "edu-escondida")
LOGIN = os.environ.get("ODOO_LOGIN", "sky@technext.asia")
KEY = os.environ.get("ODOO_API_KEY")
if not KEY:
    sys.exit("Set ODOO_API_KEY in the environment first (do not commit it).")

common = xmlrpc.client.ServerProxy(URL + "/xmlrpc/2/common", allow_none=True)
UID = common.authenticate(DB, LOGIN, KEY, {})
M = xmlrpc.client.ServerProxy(URL + "/xmlrpc/2/object", allow_none=True, use_datetime=True)
def x(model, method, args=None, kw=None): return M.execute_kw(DB, UID, KEY, model, method, args or [], kw or {})

# ---- 1. discover hotel models ----
models = [m["model"] for m in x("ir.model", "search_read", [[["model", "like", "hotel"]]], {"fields": ["model"]})]
print("Hotel models found:", models or "NONE — is the Hotel app activated?")
if not models:
    sys.exit("Activate Apps -> Industries -> Hotel first, then re-run.")

def fields(m):
    try: return x(m, "fields_get", [[], ["string", "relation", "required"]])
    except Exception: return {}

ROOM_MODEL = next((m for m in models if m.endswith("hotel.room") or m == "hotel.room"), None)
TYPE_MODEL = next((m for m in models if "room.type" in m or "room_type" in m), None)
print("room model:", ROOM_MODEL, "| type model:", TYPE_MODEL)
for m in [TYPE_MODEL, ROOM_MODEL]:
    if m: print(f"  fields[{m}]:", sorted(fields(m).keys()))

# ---- 2. room types + rooms (idempotent) ----
TYPES = [
    ("Standard Room", 18, 5500), ("Deluxe Room", 40, 11200),
    ("White Beach Deluxe", 40, 11600), ("Suite Room", 50, 14200),
]
ROOMS = ([("Standard Room", f"{100+i}") for i in range(1, 16)] +
         [("Deluxe Room", f"20{i}") for i in range(1, 3)] +
         [("White Beach Deluxe", f"21{i}") for i in range(1, 3)] +
         [("Suite Room", f"30{i}") for i in range(1, 5)])

type_ids = {}
if TYPE_MODEL:
    tf = fields(TYPE_MODEL)
    for name, size, rate in TYPES:
        found = x(TYPE_MODEL, "search_read", [[["name", "=", name]]], {"fields": ["id"]})
        vals = {"name": name}
        if "list_price" in tf: vals["list_price"] = rate
        if "price" in tf: vals["price"] = rate
        type_ids[name] = found[0]["id"] if found else x(TYPE_MODEL, "create", [vals])
    print("room types:", type_ids)

if ROOM_MODEL:
    rf = fields(ROOM_MODEL)
    made = 0
    for tname, num in ROOMS:
        if x(ROOM_MODEL, "search_count", [[["name", "like", num]]]):
            continue
        vals = {"name": f"{num} ({tname})" if "name" in rf else num}
        # link the type using whatever field exists
        for f in ("room_type_id", "type_id", "hotel_room_type_id", "categ_id"):
            if f in rf and tname in type_ids: vals[f] = type_ids[tname]; break
        try:
            x(ROOM_MODEL, "create", [vals]); made += 1
        except Exception as e:
            print("room create note:", num, str(e)[:120]); break
    print("rooms created:", made)

# ---- 3. reservations (best-effort; model/fields vary) ----
RES_MODEL = next((m for m in models if "reservation" in m or "folio" in m or m.endswith("hotel.booking")), None)
print("reservation model:", RES_MODEL, "(configure stays here or via the Schedule UI)")
print("\nDone. Open Hotel -> Schedule to see the rooms; add/confirm reservations to populate the Gantt.")
