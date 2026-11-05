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
