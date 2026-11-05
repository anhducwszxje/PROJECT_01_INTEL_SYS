def architecture():
    return nn.Sequential(nn.Linear(21, 64), nn.ReLU(), nn.Dropout(.15),
                         nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1))
