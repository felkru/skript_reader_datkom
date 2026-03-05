import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.text_to_speech import generate_audio

class TestTTSResilience(unittest.TestCase):

    @patch("src.text_to_speech.genai.Client")
    def test_retry_on_dns_error(self, mock_client_class):
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Simulate a DNS resolution error
        mock_client.models.generate_content_stream.side_effect = Exception("NameResolutionError: Failed to resolve 'oauth2.googleapis.com'")
        
        # Call generate_audio (should fail after retries)
        with patch("time.sleep") as mock_sleep: # Mock sleep to speed up test
            result = generate_audio("test text", "dummy_path", max_retries=2)
            
        # Verify it was called 3 times (1 initial + 2 retries)
        self.assertEqual(mock_client.models.generate_content_stream.call_count, 3)
        self.assertFalse(result)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("src.text_to_speech.genai.Client")
    def test_success_after_retry(self, mock_client_class):
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # First call fails, second succeeds
        mock_chunk = MagicMock()
        mock_chunk.parts = [MagicMock(inline_data=MagicMock(data=b"audio_data", mime_type="audio/wav"))]
        
        mock_client.models.generate_content_stream.side_effect = [
            Exception("DNS Error"),
            [mock_chunk]
        ]
        
        with patch("time.sleep"), patch("src.text_to_speech.save_binary_file") as mock_save:
            result = generate_audio("test text", "dummy_path", max_retries=2)
            
        self.assertTrue(result)
        self.assertEqual(mock_client.models.generate_content_stream.call_count, 2)
        mock_save.assert_called_once()

if __name__ == "__main__":
    unittest.main()
