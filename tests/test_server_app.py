import unittest

from fastapi.testclient import TestClient

from server.app import app


client = TestClient(app)


class ServerAppTests(unittest.TestCase):
    def test_reset_returns_observation(self) -> None:
        response = client.post("/reset", params={"task": "easy"})

        self.assertEqual(response.status_code, 200)

        body = response.json()
        self.assertEqual(body["time_step"], 0)
        self.assertEqual(len(body["requests"]), 2)
        self.assertEqual(len(body["helpers"]), 2)

    def test_grader_returns_real_score_shape(self) -> None:
        client.post("/reset", params={"task": "easy"})
        client.post(
            "/step",
            json={"action_type": "assign", "helper_id": "H1", "request_id": "R1"},
        )

        response = client.get("/grader")

        self.assertEqual(response.status_code, 200)
        self.assertIn("score", response.json())


if __name__ == "__main__":
    unittest.main()
