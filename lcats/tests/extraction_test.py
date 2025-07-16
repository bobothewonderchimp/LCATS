import unittest
from unittest.mock import Mock
from lcats import extraction


class TestExtraction(unittest.TestCase):

    def setUp(self):
        self.story = "Alice opened the door and stepped into a world of wonder."

        self.template = extraction.ExtractionTemplate(
            name="test-template",
            system_template="System prompt here.",
            user_template="Story to process:\n\"\"\"{story_text}\"\"\""
        )

        self.valid_response_json = {
            "events": [
                {"type": "scene", "text": "Alice opened the door."},
                {"type": "none", "text": "She stepped into a world of wonder."}
            ]
        }

        self.fake_client = Mock()
        self.fake_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content='{"events": ['
                                               '{"type": "scene", "text": "Alice opened the door."}, '
                                               '{"type": "none", "text": "She stepped into a world of wonder."}'
                                               ']}'))]
        )

    def test_prompt_template_renders_correctly(self):
        messages = self.template.build_prompt(self.story)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Story to process", messages[1]["content"])
        self.assertIn(self.story, messages[1]["content"])

    def test_extract_successful(self):
        result = extraction.extract_from_story(
            story_text=self.story,
            template=self.template,
            client=self.fake_client
        )
        self.assertEqual(result.model_name, "gpt-3.5-turbo")
        self.assertEqual(len(result.events), 2)
        self.assertIsNone(result.parsing_error)
        self.assertIsNone(result.extraction_error)
        self.assertEqual(result.events[0]["type"], "scene")

    def test_extract_fails_on_invalid_json(self):
        # Patch the client's output to return invalid JSON
        message = self.fake_client.chat.completions.create.return_value.choices[0].message
        message.content = "this is not JSON"
        result = extraction.extract_from_story(
            story_text=self.story,
            template=self.template,
            client=self.fake_client
        )
        self.assertIsNone(result.parsed_output)
        self.assertIsNotNone(result.parsing_error)
        self.assertIn("Failed to parse JSON", result.extraction_error)

    def test_extract_fails_on_missing_events_key(self):
        # Return valid JSON but missing "events"
        message = self.fake_client.chat.completions.create.return_value.choices[0].message
        message.content = '{"not_events": []}'
        result = extraction.extract_from_story(
            story_text=self.story,
            template=self.template,
            client=self.fake_client
        )
        self.assertIsNotNone(result.parsed_output)
        self.assertEqual(result.events, [])
        self.assertIn("missing 'events' key", result.extraction_error)

    def test_summary_and_validation(self):
        result = extraction.extract_from_story(
            story_text=self.story,
            template=self.template,
            client=self.fake_client
        )
        summary = result.summary()
        self.assertIn("Model: gpt-3.5-turbo", summary)
        self.assertIn("Events extracted: 2", summary)

        self.assertEqual(result.validate_events(), [])


if __name__ == "__main__":
    unittest.main()
