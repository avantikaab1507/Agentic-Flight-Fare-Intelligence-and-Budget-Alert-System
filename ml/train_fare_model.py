import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from joblib import dump


# --------------------------------------------------
# 1. Load dataset
# --------------------------------------------------

DATA_PATH = "data/full_fare.csv"
MODEL_PATH = "ml/fare_prediction_model.joblib"

df = pd.read_csv(DATA_PATH)

print("Dataset loaded successfully.")
print(f"Number of rows: {len(df)}")
print(f"Number of columns: {len(df.columns)}")


# --------------------------------------------------
# 2. Define features and target
# --------------------------------------------------

X = df[
    [
        "Route",
        "Airline",
        "Year",
        "Direction"
    ]
]

y = df["Price"]


# --------------------------------------------------
# 3. Define feature types
# --------------------------------------------------

categorical_features = [
    "Route",
    "Airline",
    "Direction"
]

numerical_features = [
    "Year"
]


# --------------------------------------------------
# 4. Preprocessing
# --------------------------------------------------

preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features
        ),
        (
            "numerical",
            "passthrough",
            numerical_features
        )
    ]
)


# --------------------------------------------------
# 5. Train/Test split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# --------------------------------------------------
# 6. Create Random Forest model
# --------------------------------------------------

model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    max_depth=10,
    min_samples_leaf=2
)


# --------------------------------------------------
# 7. Create complete ML pipeline
# --------------------------------------------------

pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            model
        )
    ]
)


# --------------------------------------------------
# 8. Train the model
# --------------------------------------------------

print("\nTraining Random Forest model...")

pipeline.fit(
    X_train,
    y_train
)

print("Model training completed.")


# --------------------------------------------------
# 9. Make predictions
# --------------------------------------------------

y_pred = pipeline.predict(X_test)


# --------------------------------------------------
# 10. Evaluate model
# --------------------------------------------------

mae = mean_absolute_error(
    y_test,
    y_pred
)

rmse = mean_squared_error(
    y_test,
    y_pred
) ** 0.5

r2 = r2_score(
    y_test,
    y_pred
)


print("\n========== MODEL EVALUATION ==========")

print(f"MAE  : ₹{mae:.2f}")
print(f"RMSE : ₹{rmse:.2f}")
print(f"R²   : {r2:.4f}")


# --------------------------------------------------
# 11. Display sample predictions
# --------------------------------------------------

results = X_test.copy()

results["Actual Price"] = y_test.values
results["Predicted Price"] = y_pred

print("\n========== SAMPLE PREDICTIONS ==========")

print(
    results.head(10).to_string(
        index=False
    )
)


# --------------------------------------------------
# 12. Save trained pipeline
# --------------------------------------------------

dump(
    pipeline,
    MODEL_PATH
)

print(
    f"\nTrained model saved successfully to: {MODEL_PATH}"
)