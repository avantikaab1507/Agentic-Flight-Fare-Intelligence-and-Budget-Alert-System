import json
import os
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "Duffel___Flight_Offers_Search.json"
OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "duffel_offers_clean.csv"
)


# ============================================================
# LOAD DUFFEL JSON
# ============================================================

print("Loading Duffel flight data...")

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    raw_data = json.load(file)


# ============================================================
# EXTRACT DUFFEL RESPONSE
# ============================================================

# The saved file is an n8n item structure:
#
# [
#     {
#         "json": {
#             "data": {
#                 "offers": [...]
#             }
#         }
#     }
# ]

if not isinstance(raw_data, list) or len(raw_data) == 0:
    raise ValueError(
        "Unexpected JSON structure: expected a non-empty list."
    )


duffel_response = raw_data[0].get("json", {})

offers = (
    duffel_response
    .get("data", {})
    .get("offers", [])
)


print(f"Total offers found: {len(offers)}")


# ============================================================
# PROCESS OFFERS
# ============================================================

cleaned_offers = []


for offer in offers:

    # --------------------------------------------------------
    # FILTER SYNTHETIC DUFFEL TEST AIRLINE
    # --------------------------------------------------------

    airline_code = (
        offer.get("owner", {})
        .get("iata_code")
    )

    airline_name = (
        offer.get("owner", {})
        .get("name")
    )

    if (
        airline_code == "ZZ"
        or airline_name == "Duffel Airways"
    ):
        continue


    # --------------------------------------------------------
    # BASIC OFFER INFORMATION
    # --------------------------------------------------------

    offer_id = offer.get("id")

    price = offer.get("total_amount")

    currency = offer.get("total_currency")


    # --------------------------------------------------------
    # SLICES
    # --------------------------------------------------------

    slices = offer.get("slices", [])

    if not slices:
        continue


    first_slice = slices[0]

    segments = first_slice.get("segments", [])

    if not segments:
        continue


    # --------------------------------------------------------
    # FIRST SEGMENT
    # --------------------------------------------------------

    first_segment = segments[0]

    last_segment = segments[-1]


    # --------------------------------------------------------
    # ROUTE
    # --------------------------------------------------------

    origin = (
        first_segment
        .get("origin", {})
        .get("iata_code")
    )

    destination = (
        last_segment
        .get("destination", {})
        .get("iata_code")
    )


    # --------------------------------------------------------
    # DEPARTURE / ARRIVAL
    # --------------------------------------------------------

    departure_time = (
        first_segment
        .get("departing_at")
    )

    arrival_time = (
        last_segment
        .get("arriving_at")
    )


    # --------------------------------------------------------
    # DURATION
    # --------------------------------------------------------

    duration = first_slice.get("duration")


    # Convert ISO duration such as:
    # PT7H58M
    #
    # into minutes.

    duration_minutes = None

    if duration:

        try:

            duration_text = duration

            hours = 0
            minutes = 0

            if "H" in duration_text:

                hour_part = (
                    duration_text
                    .split("H")[0]
                    .replace("PT", "")
                )

                hours = int(hour_part)


            if "M" in duration_text:

                minute_part = (
                    duration_text
                    .split("H")[-1]
                    .replace("M", "")
                    .replace("PT", "")
                )

                if minute_part:
                    minutes = int(minute_part)


            duration_minutes = (
                hours * 60
                + minutes
            )

        except (ValueError, TypeError):

            duration_minutes = None


    # --------------------------------------------------------
    # STOPS
    # --------------------------------------------------------

    number_of_segments = len(segments)

    stops = max(
        number_of_segments - 1,
        0
    )


    # --------------------------------------------------------
    # CABIN CLASS
    # --------------------------------------------------------

    cabin_class = None

    passengers = (
        first_segment
        .get("passengers", [])
    )

    if passengers:

        cabin_class = (
            passengers[0]
            .get("cabin_class")
        )


    # --------------------------------------------------------
    # DEPARTURE DATE / HOUR
    # --------------------------------------------------------

    departure_date = None
    departure_hour = None

    if departure_time:

        try:

            departure_timestamp = pd.to_datetime(
                departure_time
            )

            departure_date = (
                departure_timestamp.date()
                .isoformat()
            )

            departure_hour = (
                departure_timestamp.hour
            )

        except Exception:

            departure_date = None
            departure_hour = None


    # --------------------------------------------------------
    # ADD CLEAN RECORD
    # --------------------------------------------------------

    cleaned_offers.append({

        "offer_id": offer_id,

        "airline": airline_name,

        "airline_code": airline_code,

        "origin": origin,

        "destination": destination,

        "departure_date": departure_date,

        "departure_hour": departure_hour,

        "departure_time": departure_time,

        "arrival_time": arrival_time,

        "duration_minutes": duration_minutes,

        "stops": stops,

        "cabin_class": cabin_class,

        "price": (
            float(price)
            if price is not None
            else None
        ),

        "currency": currency

    })


# ============================================================
# CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(
    cleaned_offers
)


# ============================================================
# BASIC DATA CLEANING
# ============================================================

if not df.empty:

    df = df.dropna(
        subset=[
            "price",
            "currency",
            "origin",
            "destination"
        ]
    )

    df = df.reset_index(
        drop=True
    )


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ============================================================
# SAVE CLEAN DATASET
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

print()
print("==============================================")
print("FARE DATA PREPARATION COMPLETE")
print("==============================================")

print(
    f"Original offers: {len(offers)}"
)

print(
    f"Clean offers:    {len(df)}"
)

print(
    f"Removed offers:  {len(offers) - len(df)}"
)

print()

print(
    f"Saved dataset: {OUTPUT_FILE}"
)

print()

print("Dataset columns:")

for column in df.columns:

    print(
        f" - {column}"
    )

print()

print("First 5 records:")

print(
    df.head().to_string(
        index=False
    )
)

print()

print("Fare currencies:")

print(
    df["currency"]
    .value_counts()
    .to_string()
)

print()

print("Airlines found:")

print(
    df["airline"]
    .value_counts()
    .to_string()
)

print()

print("==============================================")
print("DONE")
print("==============================================")