"""Q-learning reminder simulator. Rewards are assumptions, not health outcomes."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from diabetes_agent.config import ARTIFACTS

ACTIONS = ["Không nhắc", "Nhắc ghi nhật ký", "Gửi gợi ý ghi chép ngắn"]


def transition(state, action, rng):
    gap, fatigue = divmod(int(state), 2)
    # Synthetic response probability; coefficients are author-defined assumptions.
    probability = np.clip(.40 - .07 * gap - .08 * fatigue + [.0, .35, .22][action], .05, .95)
    logged = bool(rng.random() < probability)
    next_gap = 0 if logged else min(3, gap + 1)
    next_fatigue = int(rng.random() < ([.15, .70, .40][action]))
    reward = float(logged) - [.0, .22, .10][action] - .10 * next_gap - .12 * fatigue * (action > 0)
    return 2 * next_gap + next_fatigue, reward, logged


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


def evaluate_policy(policy, seeds=range(10000, 10200)):
    rows = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        state, total, logs, reminders = int(rng.integers(8)), 0., 0, 0
        for _ in range(28):
            action = int(policy(state))
            state, reward, logged = transition(state, action, rng)
            total += reward; logs += logged; reminders += action > 0
        rows.append({"eval_seed": seed, "reward_per_day": total / 28,
                     "logging_rate": logs / 28, "reminder_rate": reminders / 28})
    return pd.DataFrame(rows)


def run_experiment():
    all_rows, histories, policies = [], [], []
    for seed in (42, 43, 44, 45, 46):
        q, history = train_q(seed)
        policies.append(q.argmax(axis=1).tolist())
        histories.append(history)
        if seed == 42:
            np.save(ARTIFACTS / "q_table.npy", q)
        for name, policy in {"q_learning": lambda s: q[s].argmax(),
                             "never": lambda s: 0, "fixed": lambda s: 1,
                             "rule": lambda s: 1 if s // 2 >= 2 and s % 2 == 0 else 0}.items():
            result = evaluate_policy(policy)
            result["policy"], result["train_seed"] = name, seed
            all_rows.append(result)
    details = pd.concat(all_rows, ignore_index=True)
    details.to_csv(ARTIFACTS / "rl_evaluation.csv", index=False)
    history = pd.concat(histories, ignore_index=True)
    history.to_csv(ARTIFACTS / "rl_history.csv", index=False)
    summary = details.groupby(["policy", "train_seed"]).reward_per_day.mean().groupby("policy").agg(["mean", "std"])
    summary.to_csv(ARTIFACTS / "rl_summary.csv")
    (ARTIFACTS / "rl_manifest.json").write_text(json.dumps({"states": 8, "actions": ACTIONS,
        "episodes": 1800, "days": 28, "gamma": .92, "alpha": .08,
        "train_seeds": [42, 43, 44, 45, 46], "evaluation_seeds": [10000, 10199],
        "policies": policies, "limitation": "Synthetic reminder response and utility; not treatment efficacy."},
        ensure_ascii=False, indent=2), encoding="utf-8")
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.7))
    for seed, h in history.groupby("seed"):
        axes[0].plot(h.episode, h.reward_per_day.rolling(100).mean(), label=str(seed), alpha=.75)
    axes[0].set(xlabel="Episode", ylabel="Reward/day (100-episode mean)", title="Synthetic reminder learning")
    axes[0].legend(fontsize=7)
    axes[1].bar(summary.index, summary["mean"], yerr=summary["std"].fillna(0), color="#176b68")
    axes[1].set(ylabel="Mean reward/day", title="200 evaluation rollouts per train seed")
    fig.tight_layout(); fig.savefig(ARTIFACTS / "figures" / "rl.png", dpi=170); plt.close(fig)
    return summary
