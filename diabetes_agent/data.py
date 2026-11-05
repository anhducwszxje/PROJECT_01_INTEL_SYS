"""Read a frozen, documented CDC study subset; enforce split isolation."""
import hashlib
import json
import sqlite3

import pandas as pd

from diabetes_agent.config import ARTIFACTS, DATA, FEATURES


def load_data():
    path = DATA / "classification.csv"
    provenance = json.loads((DATA / "provenance.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != provenance["study_sha256"]:
        raise ValueError("Dataset checksum changed. Review provenance before retraining.")
    frame = pd.read_csv(path, dtype={"group": str})
    assert set(frame.target.unique()) == {0, 1}
    assert not frame[FEATURES].isna().any().any()
    groups = [set(frame.loc[frame.split == s, "group"])
              for s in ("train", "validation", "test")]
    assert all(not groups[i] & groups[j] for i in range(3) for j in range(i))
    # Independently recompute feature fingerprints rather than trusting stored IDs.
    hashes = pd.util.hash_pandas_object(frame[FEATURES], index=False)
    assert frame.assign(fingerprint=hashes).groupby("fingerprint").split.nunique().max() == 1
    return frame


def build_database():
    """SQLite is rebuildable; the distributed CSV remains the source of truth."""
    frame = load_data()
    ARTIFACTS.mkdir(exist_ok=True)
    with sqlite3.connect(ARTIFACTS / "research.sqlite3") as conn:
        frame.to_sql("health_indicators", conn, if_exists="replace", index=False)
    return frame.groupby("split").target.agg(["count", "mean"])


def read_database():
    build_database()
    with sqlite3.connect(ARTIFACTS / "research.sqlite3") as conn:
        return pd.read_sql_query("SELECT * FROM health_indicators", conn)
