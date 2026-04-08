TASKS = [
    {
        "id": "easy",
        "name": "Basic Emergency Matching",
        "difficulty": "easy",
        "description": "Match one helper to one request with direct skill alignment.",
        "max_steps": 10,
        "reset_params": {"task": "easy"},
    },
    {
        "id": "medium",
        "name": "Prioritized Limited-Helper Dispatch",
        "difficulty": "medium",
        "description": "Allocate scarce helpers across mixed-priority requests.",
        "max_steps": 10,
        "reset_params": {"task": "medium"},
    },
    {
        "id": "hard",
        "name": "Dynamic Community Assistance",
        "difficulty": "hard",
        "description": "Handle dynamic incoming requests under sustained time pressure.",
        "max_steps": 10,
        "reset_params": {"task": "hard"},
    },
]

TASKS_BY_ID = {task["id"]: task for task in TASKS}
