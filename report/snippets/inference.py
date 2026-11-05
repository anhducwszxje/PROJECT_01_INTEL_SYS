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
                "meaning": "Điểm phân loại nhãn tiền tiểu đường/tiểu đường trên dữ liệu khảo sát UCI."}
