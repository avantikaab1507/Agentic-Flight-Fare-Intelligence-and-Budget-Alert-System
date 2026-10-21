import pandas as pd
from joblib import load


# --------------------------------------------------
# 1. Load the trained model
# --------------------------------------------------

MODEL_PATH = "ml/fare_prediction_model.joblib"

model = load(MODEL_PATH)

print("Trained fare prediction model loaded successfully.")


# --------------------------------------------------
# 2. Create a new flight input
# --------------------------------------------------

new_flight = pd.DataFrame([
    {
        "Route": "Delhi ↔ Mumbai",
        "Airline": "IndiGo",
        "Year": 2023,
        "Direction": "→"
    }
])


# --------------------------------------------------
# 3. Predict fare
# --------------------------------------------------

predicted_fare = model.predict(new_flight)[0]


# --------------------------------------------------
# 4. Display prediction
# --------------------------------------------------

print("\n========== FARE PREDICTION ==========")

print("Route     :", new_flight["Route"].iloc[0])
print("Airline   :", new_flight["Airline"].iloc[0])
print("Year      :", new_flight["Year"].iloc[0])
print("Direction :", new_flight["Direction"].iloc[0])

print(f"\nPredicted historical fare: ₹{predicted_fare:.2f}")