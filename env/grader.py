def compute_score(env):
    """
    Computes final score (0.0 to 1.0)
    """

    # -----------------------------
    # 1. Success Rate
    # -----------------------------
    if env.total_requests == 0:
        success_rate = 0.0
    else:
        success_rate = env.resolved_requests / env.total_requests

    # -----------------------------
    # 2. Speed Score (lower wait = better)
    # -----------------------------
    if env.total_requests == 0:
        speed_score = 0.0
    else:
        avg_wait = env.total_wait_time / env.total_requests
        speed_score = 1 / (1 + avg_wait)

    # -----------------------------
    # 3. Trust Score
    # -----------------------------
    if len(env.used_trust_scores) == 0:
        trust_score = 0.0
    else:
        trust_score = sum(env.used_trust_scores) / len(env.used_trust_scores)

    # -----------------------------
    # Final Weighted Score
    # -----------------------------
    score = (
        0.5 * success_rate +
        0.3 * speed_score +
        0.2 * trust_score
    )

    # Clamp between 0 and 1
    score = max(0.0, min(1.0, score))

    return score