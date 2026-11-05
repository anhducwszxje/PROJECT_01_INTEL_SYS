    validation = []
    for name in [*models, "mlp"]:
        p = probabilities(name, valid)
        validation.append({"model": name, **metrics(valid.target, p, choose_threshold(valid.target, p))})
    validation = pd.DataFrame(validation)
    default = validation[validation.model != "dummy"].sort_values(
        "average_precision", ascending=False).iloc[0].model
    validation.to_csv(ARTIFACTS / "metrics_validation.csv", index=False)
    manifest = {"seed": SEED, "default_model": default, "best_epoch": best_epoch,
                "features": FEATURES, "selection": "validation average precision; validation F1 threshold",
                "thresholds": dict(zip(validation.model, validation.threshold)),
                "python": platform.python_version(), "torch": torch.__version__,
                "sklearn": sklearn.__version__, "architecture": "21 -> 64 ReLU -> 32 ReLU -> 1 logit"}
