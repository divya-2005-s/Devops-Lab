import unittest

from app import application_status


class ApplicationStatusTests(unittest.TestCase):
    def test_status_payload_has_expected_values(self):
        status = application_status()

        self.assertEqual(status["application"], "Exercise 7 demo")
        self.assertEqual(status["status"], "ok")
        self.assertIn("CI pipeline", status["message"])


if __name__ == "__main__":
    unittest.main()
