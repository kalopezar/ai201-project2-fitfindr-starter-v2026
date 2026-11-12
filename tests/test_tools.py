import unittest
from unittest.mock import patch

from tools import create_fit_card


class FitCardPromptTests(unittest.TestCase):
    def test_platform_name_is_excluded_from_hashtags(self):
        item = {
            "title": "Test listing",
            "price": 18,
            "platform": "depop",
            "category": "top",
            "condition": "good",
            "colors": ["blue"],
            "style_tags": ["casual"],
            "description": "A test listing.",
        }
        with patch("tools.generate", return_value="Test caption.") as generate:
            create_fit_card("Jeans and sneakers.", item)

        prompt = generate.call_args.args[0]
        self.assertIn("Do not use the platform name in any hashtag", prompt)
        self.assertIn("style-related hashtags unrelated to the seller", prompt)


if __name__ == "__main__":
    unittest.main()
