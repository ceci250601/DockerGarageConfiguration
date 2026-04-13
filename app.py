# =============================================================================
# app.py - Backend principale Flask per la gestione del Garage
# =============================================================================

from __future__ import annotations
import os
import json
from pathlib import Path
from dataclasses import asdict

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify
)

# Importiamo Car e CarManager dal modulo esterno
from garage_utils import Car, CarManager

# -----------------------------------------------------------------------------
# Configurazione Flask
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cambia_questa_chiave_super_segreta")

# -----------------------------------------------------------------------------
# Modello e gestione dati
# -----------------------------------------------------------------------------
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
CARS_JSON = DATA_DIR / "cars.json"
GARAGE_CONFIG_TXT = DATA_DIR / "garage_sections.txt"
APPOINTMENTS_JSON = DATA_DIR / "appointments.json"

# Usiamo CarManager di garage_utils
car_manager = CarManager(CARS_JSON)
cars = car_manager.cars

# -----------------------------------------------------------------------------
# Funzioni helper colore / luminanza
# -----------------------------------------------------------------------------
CSS_LIGHT_NAMES = {
    "white": "#ffffff", "whitesmoke": "#f5f5f5", "ghostwhite": "#f8f8ff",
    "snow": "#fffafa", "ivory": "#fffff0", "floralwhite": "#fffaf0",
    "seashell": "#fff5ee", "gainsboro": "#dcdcdc",
    "lightgray": "#d3d3d3", "lightgrey": "#d3d3d3", "silver": "#c0c0c0",
}

def _hex_to_rgb(v: str) -> tuple[int,int,int] | None:
    v = v.lstrip("#")
    if len(v) == 3:
        v = "".join(ch*2 for ch in v)
    if len(v) != 6:
        return None
    try:
        return int(v[0:2],16), int(v[2:4],16), int(v[4:6],16)
    except ValueError:
        return None

def _to_rgb(color: str) -> tuple[int,int,int] | None:
    if not color:
        return None
    c = color.strip().lower()
    if c.startswith("#"):
        return _hex_to_rgb(c)
    if c in CSS_LIGHT_NAMES:
        return _hex_to_rgb(CSS_LIGHT_NAMES[c])
    return None

def _is_light_color(color: str) -> bool:
    rgb = _to_rgb(color)
    if not rgb:
        return False
    r,g,b = [x/255.0 for x in rgb]
    def lin(c): return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4
    R,G,B = lin(r), lin(g), lin(b)
    L = 0.2126*R + 0.7152*G + 0.0722*B
    return L >= 0.80

# -----------------------------------------------------------------------------
# Rotte principali
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    # 🔹 leggi numero sezioni dal file
    try:
        with open(GARAGE_CONFIG_TXT, encoding="utf-8") as f:
            num_sections = int(f.read().strip())
    except Exception:
        num_sections = 0

    # 🔹 carica auto e appuntamenti
    try:
        with open(CARS_JSON, encoding="utf-8") as f:
            cars_data = json.load(f)
    except FileNotFoundError:
        cars_data = []

    try:
        with open(APPOINTMENTS_JSON, encoding="utf-8") as f:
            appointments = json.load(f)
    except FileNotFoundError:
        appointments = []

    # 🔹 dizionario { model → dati auto }
    cars_by_model = {car["model"]: car for car in cars_data}

    # 🔹 unisci dati auto + appuntamenti
    garage_sections = []
    for appt in appointments:
        model = appt["car"]
        car_info = cars_by_model.get(model, {})
        color = car_info.get("color", "#000000")
        needs_border = _is_light_color(color)

        departure = "idle" if appt["mode"] == "idle" else f"depart - {appt['time']}"

        garage_sections.append({
            "model": model,
            "departure": departure,
            "color": color,
            "brand": car_info.get("brand", ""),
            "disabled": car_info.get("disabled", False),
            "needs_border": needs_border,
            "mode": appt["mode"],
            "time": appt["time"],
        })

    # 🔹 ordina (prima depart per orario crescente, poi idle in fondo)
    def sort_key(item):
        if item["mode"] == "idle":
            return (1, "99:99")
        return (0, item["time"] or "99:99")

    garage_sections.sort(key=sort_key)
    garage_sections = list(reversed(garage_sections))  # inverti per idle in basso

    # 🔹 completa con sezioni vuote fino a num_sections
    while len(garage_sections) < num_sections:
        garage_sections.append(None)

    return render_template(
        "index.html",
        garage_sections=garage_sections,
        num_sections=num_sections
    )

# -----------------------------------------------------------------------------
# Calendario
# -----------------------------------------------------------------------------
@app.route("/calendar", methods=["GET"])
def calendar_view():
    """Pagina calendario con auto abilitate (non disabilitate)."""
    enabled_cars = [asdict(c) for c in cars if not c.disabled]
    return render_template("calendar.html", cars=enabled_cars)

@app.route("/calendar/save", methods=["POST"])
def calendar_save():
    """Salva configurazione calendario in appointments.json"""
    try:
        data = request.get_json(force=True)

        if not isinstance(data, list):
            return jsonify({"error": "Formato non valido: attesa lista"}), 400

        valid_entries = []
        for entry in data:
            car = entry.get("car")
            mode = entry.get("mode")
            time = entry.get("time", "").strip()

            if not car or not mode:
                return jsonify({"error": f"Dati incompleti per {entry}"}), 400

            if mode == "depart" and not time:
                return jsonify({"error": f"Nessun orario per l'auto {car}"}), 400
            if mode == "idle":
                time = ""

            valid_entries.append({
                "car": car,
                "mode": mode,
                "time": time
            })

        sorted_data = sorted(
            valid_entries,
            key=lambda x: (
                0 if x["mode"] == "depart" else 1,
                x["time"] if x["mode"] == "depart" else "99:99"
            )
        )

        APPOINTMENTS_JSON.write_text(
            json.dumps(sorted_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return jsonify({"status": "ok", "saved": sorted_data})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------------------------
# Rotte gestione auto
# -----------------------------------------------------------------------------
@app.route("/select_cars", methods=["GET", "POST"])
def select_cars():
    """Pagina di gestione auto: aggiunta e lista."""
    if request.method == "POST":
        data = request.form
        try:
            car = Car(
                brand=data.get("brand", "").strip(),
                model=data.get("model", "").strip(),
                color=data.get("color", "").strip(),
                disabled=(data.get("disabled") == "true"),
            )
            car_manager.cars.append(car)
            car_manager.save()
            flash("Auto aggiunta correttamente!", "success")
        except Exception as e:
            flash(f"Errore durante l'aggiunta: {e}", "error")
        return redirect(url_for("select_cars"))
    return render_template("select_cars.html", cars=cars)

@app.route("/select_cars/remove/<int:index>")
def remove_car(index: int):
    """Rimuove auto dall'elenco."""
    try:
        car_manager.cars.pop(index)
        car_manager.save()
        flash("Auto rimossa.", "info")
    except IndexError:
        flash("Auto non trovata.", "error")
    return redirect(url_for("select_cars"))

@app.route("/select_cars/edit/<int:index>", methods=["GET", "POST"])
def edit_car(index: int):
    """Modifica dati auto."""
    if index < 0 or index >= len(cars):
        flash("Auto non trovata.", "error")
        return redirect(url_for("select_cars"))
    car = car_manager.cars[index]
    if request.method == "POST":
        try:
            car.brand = (request.form.get("brand") or "").strip()
            car.model = (request.form.get("model") or "").strip()
            car.color = (request.form.get("color") or "").strip()
            car.disabled = (request.form.get("disabled") == "true")
            car_manager.save()
            flash("Auto aggiornata correttamente!", "success")
            return redirect(url_for("select_cars"))
        except Exception as e:
            flash(f"Errore durante l'aggiornamento: {e}", "error")
    return render_template("edit_car.html", car=car, index=index)

@app.route("/cars")
def cars_view():
    """Visualizza elenco auto in formato tabellare."""
    return render_template("cars.html", cars=cars)

@app.route("/edit_sections", methods=["GET", "POST"])
def edit_sections():
    """Gestione numero sezioni garage."""
    try:
        current = int(GARAGE_CONFIG_TXT.read_text(encoding="utf-8").strip())
    except Exception:
        current = 0
    if request.method == "POST":
        raw = (request.form.get("num_sections") or "").strip()
        try:
            n = int(raw)
            if n < 0:
                raise ValueError("Il numero di sezioni non può essere negativo.")
            GARAGE_CONFIG_TXT.write_text(str(n), encoding="utf-8")
            flash("Numero sezioni aggiornato.", "success")
            return redirect(url_for("edit_sections"))
        except Exception as e:
            flash(f"Valore non valido: {e}", "error")
            return render_template("edit_sections.html", current=current)
    return render_template("edit_sections.html", current=current)

# -----------------------------------------------------------------------------
# Avvio server
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
