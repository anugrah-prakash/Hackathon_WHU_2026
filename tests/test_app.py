"""Streamlit smoke tests; skipped only when Streamlit is not installed."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

STREAMLIT_AVAILABLE = importlib.util.find_spec("streamlit") is not None


@unittest.skipUnless(STREAMLIT_AVAILABLE, "Streamlit is not installed in this environment")
class AppSmokeTests(unittest.TestCase):
    def app(self):
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))

    def test_initial_page_and_disabled_submit(self):
        with patch("medeasy.config.settings", return_value=("", "test/model")):
            app = self.app().run()
        self.assertEqual(len(app.exception), 0)
        submit = next(button for button in app.button if button.label == "Explain my letter →")
        self.assertTrue(submit.disabled)

    def test_example_requires_consent(self):
        with patch("medeasy.config.settings", return_value=("", "test/model")):
            app = self.app().run()
            app.radio[0].set_value("Try an example").run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn("MED-2026-0042", app.text_area[0].value)
            submit = next(button for button in app.button if button.label == "Explain my letter →")
            self.assertTrue(submit.disabled)
            app.checkbox[0].check().run()
            submit = next(button for button in app.button if button.label == "Explain my letter →")
            self.assertFalse(submit.disabled)
            submit.click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("API key" in error.value for error in app.error))

    def test_camera_option_renders_without_text(self):
        with patch("medeasy.config.settings", return_value=("", "test/model")):
            app = self.app().run()
            app.radio[0].set_value("Take a picture").run()
            self.assertEqual(len(app.exception), 0)
            self.assertTrue(any("Check and correct" in area.label for area in app.text_area))
            submit = next(button for button in app.button if button.label == "Explain my letter →")
            self.assertTrue(submit.disabled)

    def test_clear_resets_letter(self):
        with patch("medeasy.config.settings", return_value=("", "test/model")):
            app = self.app().run()
            app.text_area[0].set_value("Private text").run()
            next(button for button in app.button if button.label == "Clear this letter").click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.text_area[0].value, "")


if __name__ == "__main__":
    unittest.main()
