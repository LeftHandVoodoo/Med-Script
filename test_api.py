import unittest
from api.openai_integration import fetch_medication_info

class TestOpenAIIntegration(unittest.TestCase):
    def test_fetch_medication_info(self):
        try:
            # Replace 'Ibuprofen' with a known medication for testing
            response = fetch_medication_info('Ibuprofen')
            self.assertIn('Ibuprofen', response)  # Check if response contains the medication name
        except Exception as e:
            self.fail(f'API request failed: {str(e)}')

if __name__ == '__main__':
    unittest.main()