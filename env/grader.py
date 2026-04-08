def compute_score(env):
    # Return default baseline if env hasn't been used
    if env.total_requests == 0:
        return 0.5  # neutral baseline score

    success_rate = env.resolved_requests / env.total_requests

    avg_wait = env.total_wait_time / env.total_requests
    speed_score = 1 / (1 + avg_wait)

    if len(env.used_trust_scores) == 0:
        trust_score = 0.5
    else:
        trust_score = sum(env.used_trust_scores) / len(env.used_trust_scores)

    score = (
        0.5 * success_rate +
        0.3 * speed_score +
        0.2 * trust_score
    )

    return max(0.0, min(1.0, score))