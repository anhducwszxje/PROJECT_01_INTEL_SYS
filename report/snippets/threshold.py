def choose_threshold(y, p):
    candidates = np.linspace(.05, .8, 151)
    # Ties resolve to the first threshold; all candidates are validation-only.
    return float(max(candidates, key=lambda t: f1_score(y, p >= t, zero_division=0)))
