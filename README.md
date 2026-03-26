---
title: AssistOpsEnv
emoji: 🚑
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---


# AssistOpsEnv: AI Environment for Community Emergency Assistance

## Overview

AssistOpsEnv is a real-world simulation environment designed to model community-driven emergency assistance systems. It enables AI agents to learn how to efficiently assign available helpers to incoming requests under constraints such as time, trust, and resource limitations.

This environment follows the OpenEnv specification and supports reinforcement learning-style interaction via `reset()` and `step()` APIs.

---

## Motivation

In real-life scenarios, emergency assistance often suffers due to delays, inefficient allocation, and lack of coordination. This environment allows AI agents to learn optimal strategies for:

* Assigning the right helper to the right request
* Minimizing response time
* Prioritizing critical cases
* Maintaining trust and reliability

---

## Environment Design

### Observation Space

Each observation contains:

* `time_step`: Current timestep
* `requests`: List of active requests

  * id, type, severity, waiting_time, assigned, resolved
* `helpers`: List of available helpers

  * id, skills, trust_score, busy status, current_request, time_to_complete

---

### Action Space

Agents can perform two types of actions:

#### Assign Action

```json
{
  "action_type": "assign",
  "helper_id": "H1",
  "request_id": "R1"
}
```

#### Wait Action

```json
{
  "action_type": "wait"
}
```

---

## Reward Function

The reward function provides meaningful feedback:

* +1 for correct skill match
* -1 for incorrect assignment
* * (1 + 0.5 × severity) for successful completion
* -0.1 × severity for unassigned waiting requests
* Penalty for invalid actions

This encourages both correctness and efficiency.

---

## Tasks

### Easy Task

* Equal helpers and requests
* Direct mapping possible
* Tests correctness

### Medium Task

* Limited helpers
* Multiple similar requests
* Requires prioritization

### Hard Task

* Dynamic request generation
* Limited helpers
* Increasing workload
* Simulates real-world pressure

---

## Grader

Performance is evaluated using:

* **Success Rate (50%)** → resolved / total requests
* **Speed Score (30%)** → based on waiting time
* **Trust Score (20%)** → based on helper trust

Final score ranges from **0.0 to 1.0**.

---

## Baseline Agent

A simple heuristic-based agent:

* Assigns the first available helper to the first unassigned request
* Waits when no valid assignment is possible

Example results:

```
EASY SCORE: ~0.85+
MEDIUM SCORE: ~0.7+
HARD SCORE: ~0.5+
```

---

## API Endpoints

* `POST /reset` → Initialize environment
* `POST /step` → Execute action
* `GET /state` → Get current state
* `GET /tasks` → List available tasks
* `GET /grader` → Compute final score

---

## Setup Instructions

### Run Locally

```bash
uvicorn api.main:app --reload
```

Open:
http://127.0.0.1:8000/docs

---

### Run with Docker

```bash
docker build -t assist-ops-env .
docker run -p 7860:7860 assist-ops-env
```

Open:
http://127.0.0.1:7860/docs

---

## Project Structure

```
assist_ops_env/
│
├── env/            # Core environment logic
├── api/            # FastAPI endpoints
├── baseline/       # Baseline agent
│
├── Dockerfile
├── openenv.yaml
└── README.md
```

---

## Key Features

* Real-world simulation (not a toy problem)
* Dynamic environment with time progression
* Multi-task difficulty levels
* Meaningful reward shaping
* Deterministic grading system
* Fully containerized deployment

---

## Future Improvements

* Multi-agent coordination
* Location-based matching
* Learning-based helper ranking
* Integration with real-world datasets

---

## Conclusion

AssistOpsEnv provides a realistic and scalable environment for training and evaluating AI agents in emergency response systems. It bridges the gap between simulation and real-world applicability, making it valuable for both research and practical deployment.
