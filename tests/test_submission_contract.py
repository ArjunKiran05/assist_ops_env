import unittest

from fastapi.testclient import TestClient

from server.app import app


client = TestClient(app)


class SubmissionContractTests(unittest.TestCase):
    def test_reset_matches_openenv_response_shape(self) -> None:
        response = client.post("/reset", json={"task": "easy"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("observation", body)
        self.assertIn("reward", body)
        self.assertIn("done", body)
        self.assertEqual(body["done"], False)
        self.assertEqual(body["observation"]["time_step"], 0)

    def test_tasks_expose_three_graded_tasks(self) -> None:
        response = client.get("/tasks")

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertIn("tasks", body)
        tasks = body["tasks"]
        self.assertEqual(len(tasks), 3)

        for task in tasks:
            self.assertIn("id", task)
            self.assertIn("name", task)
            self.assertIn("difficulty", task)
            self.assertIn("description", task)
            self.assertIn("grader", task)
            self.assertTrue(task["grader"])
            self.assertIn("grader_endpoint", task)
            self.assertTrue(task["grader_endpoint"].startswith("/grade/"))

    def test_grader_supports_task_query(self) -> None:
        response = client.get("/grader", params={"task": "easy"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["task"], "easy")
        self.assertIn("score", body)

    def test_task_specific_grade_endpoint_exists(self) -> None:
        response = client.get("/grade/easy")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["task_id"], "easy")
        self.assertEqual(body["grader"], "grade_easy")
        self.assertIn("score", body)

    def test_post_grader_accepts_task_id(self) -> None:
        response = client.post("/grader", json={"task_id": "easy", "run_output": {"success": True}})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["task_id"], "easy")
        self.assertEqual(body["score"], 1.0)

    def test_runtime_uses_real_environment_flow(self) -> None:
        reset_response = client.post("/reset", json={"task": "easy"})
        self.assertEqual(reset_response.status_code, 200)

        step_response = client.post(
            "/step",
            json={"action_type": "assign", "helper_id": "H1", "request_id": "R1"},
        )

        self.assertEqual(step_response.status_code, 200)
        step_body = step_response.json()
        self.assertIn("observation", step_body)
        self.assertIn("reward", step_body)
        self.assertIn("done", step_body)

    def test_standard_wrapped_step_payload_is_supported(self) -> None:
        client.post("/reset", json={"task": "easy"})

        response = client.post(
            "/step",
            json={
                "action": {
                    "action_type": "assign",
                    "helper_id": "H1",
                    "request_id": "R1",
                }
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("observation", response.json())

    def test_validate_reports_three_tasks_with_graders(self) -> None:
        response = client.get("/validate")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["valid"])
        self.assertEqual(body["task_count"], 3)
        self.assertEqual(body["graders_count"], 3)


if __name__ == "__main__":
    unittest.main()
