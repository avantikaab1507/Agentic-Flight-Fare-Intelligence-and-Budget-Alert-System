
from flask import Flask, request, jsonify
from joblib import load
import pandas as pd

app = Flask(__name__)

MODEL_PATH = "ml/fare_prediction_model.joblib"
DATA_PATH = "data/full_fare.csv"


# --------------------------------------------------
# LOAD MODEL AND HISTORICAL DATA
# --------------------------------------------------

model = load(MODEL_PATH)
training_data = pd.read_csv(DATA_PATH)

print("Fare prediction model loaded successfully.")
print("Training dataset loaded successfully.")
print(f"Training records available: {len(training_data)}")


# --------------------------------------------------
# NORMALIZE ROUTE AND DIRECTION TEXT
# --------------------------------------------------

def normalize_route(value):
    if value is None or pd.isna(value):
        return None

    route = str(value).strip()

    # Normalize common route-separator encoding issues.
    route = route.replace("â†”", "↔")
    route = route.replace("â†’", "↔")
    route = route.replace("â†", "↔")
    route = route.replace("?", "↔")

    return " ".join(route.split())


def normalize_direction(value):
    if value is None or pd.isna(value):
        return None

    direction = str(value).strip()

    direction_mapping = {
        "â†’": "→",
        "â†": "←",
        "?": None
    }

    return direction_mapping.get(direction, direction)


def normalize_airline(value):
    if value is None or pd.isna(value):
        return None

    airline = str(value).strip()

    airline_mapping = {
        "INDIGO": "IndiGo",
        "INDIGO AIRLINES": "IndiGo",
        "INDIGO": "IndiGo",
        "VISTARA": "Vistara",
        "AIR INDIA": "Air India",
        "SPICEJET": "SpiceJet",
        "AIRASIA": "AirAsia",
        "AIRASIA INDIA": "AirAsia"
    }

    return airline_mapping.get(airline.upper(), airline)


# Normalize values in the loaded dataset for consistent matching.
training_data["Route"] = training_data["Route"].apply(
    normalize_route
)
training_data["Airline"] = training_data["Airline"].apply(
    normalize_airline
)
training_data["Direction"] = training_data["Direction"].apply(
    normalize_direction
)


# --------------------------------------------------
# HOME / HEALTH CHECK
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "service": "Flight Fare Prediction API",
        "training_records": int(len(training_data))
    })


# --------------------------------------------------
# ML COVERAGE CHECK
# --------------------------------------------------

@app.route("/coverage", methods=["POST"])
def coverage():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A valid JSON object is required."
        }), 400

    required_fields = ["Route", "Airline"]

    missing_fields = [
        field for field in required_fields
        if field not in data
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "missing_fields": missing_fields
        }), 400

    route = normalize_route(data.get("Route"))
    airline = normalize_airline(data.get("Airline"))

    if not route or not airline:
        return jsonify({
            "covered": False,
            "route": route,
            "airline": airline,
            "matching_training_records": 0,
            "prediction_available": False,
            "reason": "Route and airline must both be provided."
        }), 200

    matching_records = training_data[
        (training_data["Route"] == route)
        & (training_data["Airline"] == airline)
    ]

    record_count = int(len(matching_records))
    covered = record_count > 0

    available_years = sorted(
        int(year)
        for year in matching_records["Year"].dropna().unique()
    )

    return jsonify({
        "covered": covered,
        "route": route,
        "airline": airline,
        "matching_training_records": record_count,
        "available_training_years": available_years,
        "prediction_available": covered,
        "reason": (
            None if covered else
            "No matching route-and-airline records were found "
            "in the training dataset."
        )
    }), 200


# --------------------------------------------------
# FARE PREDICTION
# --------------------------------------------------

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "A valid JSON object is required."
        }), 400

    required_fields = [
        "Route",
        "Airline",
        "Year",
        "Direction"
    ]

    missing_fields = [
        field for field in required_fields
        if field not in data
        or data[field] is None
        or str(data[field]).strip() == ""
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing or empty required fields",
            "missing_fields": missing_fields
        }), 400

    route = normalize_route(data["Route"])
    airline = normalize_airline(data["Airline"])
    direction = normalize_direction(data["Direction"])

    try:
        year = int(data["Year"])
    except (TypeError, ValueError):
        return jsonify({
            "error": "Year must be a valid integer."
        }), 400

    if direction not in ["→", "←"]:
        return jsonify({
            "error": "Direction must be '→' or '←'."
        }), 400

    # Check whether this route-airline combination exists.
    matching_records = training_data[
        (training_data["Route"] == route)
        & (training_data["Airline"] == airline)
    ]

    if matching_records.empty:
        return jsonify({
            "prediction_available": False,
            "reason": (
                "This route-and-airline combination is not "
                "represented in the training dataset."
            ),
            "route": route,
            "airline": airline,
            "prediction_type": None
        }), 200

    # Check the direction as well.
    matching_direction = matching_records[
        matching_records["Direction"] == direction
    ]

    if matching_direction.empty:
        return jsonify({
            "prediction_available": False,
            "reason": (
                "This travel direction is not represented "
                "for the selected route and airline."
            ),
            "route": route,
            "airline": airline,
            "direction": direction,
            "prediction_type": None
        }), 200

    # Future-year predictions are allowed for supported combinations.
    # They are extrapolations because the model was trained on 2022–2023.
    available_years = sorted(
        int(value)
        for value in training_data["Year"].dropna().unique()
    )

    is_extrapolation = year not in available_years

    input_data = pd.DataFrame([{
        "Route": route,
        "Airline": airline,
        "Year": year,
        "Direction": direction
    }])

    try:
        predicted_fare = float(model.predict(input_data)[0])
    except Exception as error:
        app.logger.exception("Fare prediction failed.")

        return jsonify({
            "error": "The fare prediction failed.",
            "details": str(error),
            "prediction_available": False
        }), 500

    return jsonify({
        "prediction_available": True,
        "predicted_fare": round(predicted_fare, 2),
        "currency": "INR",
        "route": route,
        "airline": airline,
        "year": year,
        "direction": direction,
        "prediction_type": (
            "future_year_extrapolation"
            if is_extrapolation
            else "historical_reference_fare"
        ),
        "available_training_years": available_years,
        "warning": (
            "This is an extrapolated model estimate, not a validated "
            "future fare forecast or live ticket price."
            if is_extrapolation
            else "This is a historical reference estimate, not a live ticket price."
        )
    }), 200


# --------------------------------------------------
# START FLASK SERVER
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )