from django.test import SimpleTestCase
# from .calculator import add
from .calculator import add
# Create your tests here.


class TestClass(SimpleTestCase):
    """Test making a list unique"""

    def test_make_test(self):
        # calculator.add
        result = add(1, 2)
        self.assertEqual(result, 3)
