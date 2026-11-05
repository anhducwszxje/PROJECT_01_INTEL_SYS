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
