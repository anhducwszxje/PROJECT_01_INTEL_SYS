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
