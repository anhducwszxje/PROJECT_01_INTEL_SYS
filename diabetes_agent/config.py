from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ARTIFACTS = ROOT / "artifacts"
SEED = 42
FEATURES = [
    "HighBP", "HighChol", "CholCheck", "BMI", "Smoker", "Stroke",
    "HeartDiseaseorAttack", "PhysActivity", "Fruits", "Veggies",
    "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost", "GenHlth",
    "MentHlth", "PhysHlth", "DiffWalk", "Sex", "Age", "Education", "Income",
]
# Survey codes are not physical measurements: Age is a category, not years.
BOUNDS = {name: (0, 1) for name in FEATURES}
BOUNDS.update(BMI=(12, 98), GenHlth=(1, 5), MentHlth=(0, 30),
              PhysHlth=(0, 30), Age=(1, 13), Education=(1, 6), Income=(1, 8))
DISCLAIMER = "Sản phẩm học tập; không chẩn đoán, kê đơn hoặc thay đổi điều trị."
