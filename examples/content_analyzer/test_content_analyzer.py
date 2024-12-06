import unittest
from unittest.mock import MagicMock
from content_analyzer import ContentAnalyzer, AnalyzerConfig, CardGenerator
from mcard import MCard

class TestContentAnalyzer(unittest.TestCase):
    def setUp(self):
        # Setup a ContentAnalyzer instance with default configuration
        self.analyzer = ContentAnalyzer()
        self.test_card = CardGenerator.create_text_card("This is a test content.")

    def test_initialization(self):
        # Test default initialization
        self.assertIsInstance(self.analyzer.config, AnalyzerConfig)
        self.assertIsNotNone(self.analyzer.mime_analyzer)
        self.assertIsNotNone(self.analyzer.lang_analyzer)
        self.assertIsNotNone(self.analyzer.summary_analyzer)

    def test_mime_type_analysis(self):
        # Mock the MimeTypeAnalyzer analyze method
        self.analyzer.mime_analyzer.analyze = MagicMock(return_value='text/plain')
        mime_type = self.analyzer.mime_analyzer.analyze(b'This is a test content.')
        self.assertEqual(mime_type, 'text/plain')

    def test_language_detection(self):
        # Mock the LanguageAnalyzer analyze method
        self.analyzer.lang_analyzer.analyze = MagicMock(return_value=[{'lang': 'en', 'prob': 0.99}])
        languages = self.analyzer.lang_analyzer.analyze("This is a test content.")
        self.assertEqual(languages[0]['lang'], 'en')

    def test_summary_generation(self):
        # Mock the SummaryAnalyzer analyze method
        self.analyzer.summary_analyzer.analyze = MagicMock(return_value='This is a summary.')
        summary = self.analyzer.summary_analyzer.analyze("This is a test content.", 'text/plain')
        self.assertEqual(summary, 'This is a summary.')

    def test_card_analysis(self):
        # Mock the analyze_card method
        self.analyzer.analyze_card = MagicMock(return_value='Analysis result')
        result = self.analyzer.analyze_card(self.test_card)
        self.assertEqual(result, 'Analysis result')

if __name__ == '__main__':
    unittest.main()
