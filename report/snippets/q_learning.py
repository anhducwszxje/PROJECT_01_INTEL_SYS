def train_q(seed=42, episodes=1800):
    rng = np.random.default_rng(seed)
    q = np.zeros((8, 3))
    history = []
    for episode in range(episodes):
        state, total = int(rng.integers(8)), 0.
        epsilon = max(.03, .8 * .997 ** episode)
        for day in range(28):
            action = int(rng.integers(3)) if rng.random() < epsilon else int(q[state].argmax())
            nxt, reward, _ = transition(state, action, rng)
            # The task is continuing. 28 days is a rollout window, not terminal disease state.
            q[state, action] += .08 * (reward + .92 * q[nxt].max() - q[state, action])
            state, total = nxt, total + reward
        history.append({"seed": seed, "episode": episode + 1, "reward_per_day": total / 28})
    return q, pd.DataFrame(history)
