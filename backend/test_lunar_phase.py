import unittest
import datetime
from utils.lunar_phase import get_lunar_phase

class TestLunarPhase(unittest.TestCase):
    def test_get_lunar_phase(self):
        # Test with a specific date
        test_date = datetime.date(2023, 1, 1)  # Example date
        phase = get_lunar_phase(test_date)
        
        # Verify that the result is a string and contains an emoji
        self.assertIsInstance(phase, str)
        self.assertTrue(any(emoji in phase for emoji in ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']))
        
        # Test with today's date
        today_phase = get_lunar_phase()
        self.assertIsInstance(today_phase, str)
        self.assertTrue(any(emoji in today_phase for emoji in ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']))

if __name__ == '__main__':
    unittest.main()