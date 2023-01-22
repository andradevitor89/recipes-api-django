from django.test import SimpleTestCase
from ..calculator import add, subtract


class TestClass(SimpleTestCase):
    """Test making a list unique"""

    def test_add(self):
        result = add(1, 2)
        self.assertEqual(result, 3)

    def test_subtract(self):
        result = subtract(3, 2)
        self.assertEqual(result, 1)
