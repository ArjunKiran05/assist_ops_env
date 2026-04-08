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

        tasks = response.json()
        self.assertEqual(len(tasks), 3)

        for task in tasks:
            self.assertIn("name", task)
            self.assertIn("description", task)
            self.assertIn("grader", task)
            self.assertTrue(task["grader"].startswith("/grader?task="))

    def test_grader_supports_task_query(self) -> None:
        response = client.get("/grader", params={"task": "easy"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["task"], "easy")
        self.assertIn("score", body)

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


if __name__ == "__main__":
    unittest.main()
