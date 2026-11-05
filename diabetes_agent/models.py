"""Train on train only; validation chooses epoch, model and threshold."""
import copy
import json
import platform

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
import torch
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
    roc_curve, precision_recall_curve)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch import nn

from diabetes_agent.config import ARTIFACTS, FEATURES, SEED
from diabetes_agent.data import read_database


def architecture():
    return nn.Sequential(nn.Linear(21, 64), nn.ReLU(), nn.Dropout(.15),
                         nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))


def choose_threshold(y, p):
    candidates = np.linspace(.05, .8, 151)
    # Ties resolve to the first threshold; all candidates are validation-only.
    return float(max(candidates, key=lambda t: f1_score(y, p >= t, zero_division=0)))


def metrics(y, p, threshold):
    pred = p >= threshold
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"roc_auc": float(roc_auc_score(y, p)),
            "average_precision": float(average_precision_score(y, p)),
            "f1": float(f1_score(y, pred, zero_division=0)),
            "precision": float(precision_score(y, pred, zero_division=0)),
            "recall": float(recall_score(y, pred, zero_division=0)),
            "specificity": float(tn / (tn + fp)),
            "brier": float(brier_score_loss(y, p)), "threshold": threshold,
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def plot_test_curves():
    """Plot frozen predictions; PR uses steps rather than linear interpolation."""
    manifest = json.loads((ARTIFACTS / "model_manifest.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for name in manifest["thresholds"]:
        predictions = pd.read_csv(ARTIFACTS / f"predictions_{name}.csv")
        fpr, tpr, _ = roc_curve(predictions.target, predictions.score)
        prec, rec, _ = precision_recall_curve(predictions.target, predictions.score)
        axes[0].plot(fpr, tpr, label=name)
        axes[1].step(rec, prec, where="post", label=name)
    axes[0].set(xlabel="False positive rate", ylabel="True positive rate", title="ROC - locked test")
    axes[1].set(xlabel="Recall", ylabel="Precision", title="Precision recall - locked test")
    for ax in axes:
        ax.legend(); ax.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(ARTIFACTS / "figures" / "classification.png", dpi=170); plt.close(fig)


def train_all():
    torch.set_num_threads(2)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    frame = read_database()
    train, valid, test = [frame[frame.split == s] for s in ("train", "validation", "test")]
    folder = ARTIFACTS / "models"
    folder.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "figures").mkdir(exist_ok=True)
    scaler = StandardScaler().fit(train[FEATURES])
    x = torch.tensor(scaler.transform(train[FEATURES]), dtype=torch.float32)
    xv = torch.tensor(scaler.transform(valid[FEATURES]), dtype=torch.float32)
    y = torch.tensor(train.target.to_numpy(), dtype=torch.float32).reshape(-1, 1)
    yv = torch.tensor(valid.target.to_numpy(), dtype=torch.float32).reshape(-1, 1)
    net = architecture()
    # Unweighted BCE keeps the observed training prior. No population calibration claim.
    loss_fn = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(net.parameters(), lr=.001, weight_decay=1e-4)
    best_loss, stale, best_epoch, best = float("inf"), 0, 0, None
    history = []
    for epoch in range(1, 81):
        net.train()
        order = torch.randperm(len(x))
        total = 0.
        for indexes in order.split(256):
            optimizer.zero_grad()
            loss = loss_fn(net(x[indexes]), y[indexes])
            loss.backward()
            optimizer.step()
            total += float(loss.item()) * len(indexes)
        net.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(net(xv), yv).item())
        history.append({"epoch": epoch, "train_loss": total / len(x), "validation_loss": val_loss})
        if val_loss < best_loss - 1e-5:
            best_loss, stale, best_epoch = val_loss, 0, epoch
            best = copy.deepcopy(net.state_dict())
        else:
            stale += 1
        if stale >= 10:
            break
    net.load_state_dict(best)
    net.eval()
    torch.save(best, folder / "mlp.pt")
    joblib.dump(scaler, folder / "scaler.joblib")
    pd.DataFrame(history).to_csv(ARTIFACTS / "training_history.csv", index=False)
    models = {
        "dummy": DummyClassifier(strategy="prior"),
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=SEED)),
        "random_forest": RandomForestClassifier(n_estimators=160, min_samples_leaf=8,
                                                 max_features="sqrt", n_jobs=2, random_state=SEED),
    }
    for name, model in models.items():
        model.fit(train[FEATURES], train.target)
        joblib.dump(model, folder / f"{name}.joblib")

    def probabilities(name, subset):
        if name == "mlp":
            with torch.no_grad():
                z = torch.tensor(scaler.transform(subset[FEATURES]), dtype=torch.float32)
                return torch.sigmoid(net(z)).numpy().ravel()
        return models[name].predict_proba(subset[FEATURES])[:, 1]

    # Freeze all decisions before looking at test metrics.
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
    (ARTIFACTS / "model_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    rows = []
    for row in validation.to_dict("records"):
        name, threshold = row["model"], row["threshold"]
        p = probabilities(name, test)
        rows.append({"model": name, **metrics(test.target, p, threshold)})
        pd.DataFrame({"row_id": test.row_id, "target": test.target,
                      "score": p, "predicted": (p >= threshold).astype(int)}).to_csv(
                          ARTIFACTS / f"predictions_{name}.csv", index=False)
    plot_test_curves()
    fig, ax = plt.subplots(figsize=(7, 3.4))
    h = pd.DataFrame(history)
    ax.plot(h.epoch, h.train_loss, label="Train BCE")
    ax.plot(h.epoch, h.validation_loss, label="Validation BCE")
    ax.axvline(best_epoch, linestyle="--", color="gray", label=f"Selected epoch {best_epoch}")
    ax.set(xlabel="Epoch", ylabel="BCE loss"); ax.legend(); fig.tight_layout()
    fig.savefig(ARTIFACTS / "figures" / "training.png", dpi=170); plt.close(fig)
    pd.DataFrame(rows).to_csv(ARTIFACTS / "metrics_test.csv", index=False)
    return pd.DataFrame(rows), manifest


class RiskModel:
    """Load once per application; inference never calls fit."""
    def __init__(self):
        self.manifest = json.loads((ARTIFACTS / "model_manifest.json").read_text(encoding="utf-8"))
        self.models = {n: joblib.load(ARTIFACTS / "models" / f"{n}.joblib")
                       for n in ("dummy", "logistic", "random_forest")}
        self.scaler = joblib.load(ARTIFACTS / "models" / "scaler.joblib")
        self.net = architecture()
        self.net.load_state_dict(torch.load(ARTIFACTS / "models" / "mlp.pt", map_location="cpu", weights_only=True))
        self.net.eval()

    def predict(self, profile, model="default"):
        if model == "default":
            model = self.manifest["default_model"]
        if model not in self.manifest["thresholds"]:
            raise ValueError("Unknown model")
        frame = pd.DataFrame([profile])[FEATURES]
        if model == "mlp":
            with torch.no_grad():
                x = torch.tensor(self.scaler.transform(frame), dtype=torch.float32)
                score = float(torch.sigmoid(self.net(x)).item())
        else:
            score = float(self.models[model].predict_proba(frame)[0, 1])
        threshold = self.manifest["thresholds"][model]
        return {"model": model, "score": score, "threshold": threshold,
                "positive": score >= threshold,
                "meaning": "Điểm mô hình cho nhãn gộp tiền tiểu đường/tiểu đường trong khảo sát UCI; không phải xác suất mắc bệnh trong tương lai."}
