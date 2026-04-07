def grade_easy(run_output):
    return {
        "score": 1.0 if run_output.get("success", False) else 0.0
    }


def grade_medium(run_output):
    return {
        "score": 1.0 if run_output.get("success", False) else 0.0
    }


def grade_hard(run_output):
    return {
        "score": 1.0 if run_output.get("success", False) else 0.0
    }