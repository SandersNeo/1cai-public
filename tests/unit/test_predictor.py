import unittest
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.ai.rltf.prediction.predictor import ActionPredictor


class TestActionPredictor(unittest.TestCase):
    def setUp(self):
        self.predictor = ActionPredictor()

    def test_predict_git_commit(self):
        context = {"type": "click", "tag": "BUTTON", "text": "Save Changes"}
        prediction = self.predictor.predict(context)
        self.assertIsNotNone(prediction)
        self.assertEqual(prediction["action"], "git_commit")
        self.assertGreater(prediction["confidence"], 0.8)

    def test_predict_syntax_check(self):
        context = {"type": "input", "tag": "TEXTAREA", "text": "Module.Execute()"}
        prediction = self.predictor.predict(context)
        self.assertIsNotNone(prediction)
        self.assertEqual(prediction["action"], "syntax_check")

    def test_no_prediction(self):
        context = {"type": "click", "tag": "DIV", "text": "Random Text"}
        prediction = self.predictor.predict(context)
        self.assertIsNone(prediction)


if __name__ == "__main__":
    unittest.main()
