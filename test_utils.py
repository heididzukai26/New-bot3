import unittest

import utils


class UtilsTests(unittest.TestCase):
    def test_extract_email_anywhere(self):
        message = "Hello, contact me at middle.user@example.com for details."
        self.assertEqual(utils.extract_email(message), "middle.user@example.com")
        self.assertTrue(utils.contains_email(message))

    def test_contains_email_false_when_absent(self):
        self.assertFalse(utils.contains_email("just words and numbers 1234"))

    def test_largest_number_is_max(self):
        message = "small 4 big 42 bigger 105 and smallest 1"
        self.assertEqual(utils.largest_number(message), 105)

    def test_order_rule_three_lines_email_and_number(self):
        valid = "TypeA\nDetails line with middle.user@example.com info\nAmount 50 units\nThanks"
        self.assertTrue(utils.is_order_message(valid))

        missing_lines = "TypeA\ncustomer@example.com"
        self.assertFalse(utils.is_order_message(missing_lines))

        no_email = "TypeA\nNotes\nNo email here\nAmount 50"
        self.assertFalse(utils.is_order_message(no_email))

        no_number = "TypeA\nInfo user@example.com\nMore details without number\nFinal line"
        self.assertFalse(utils.is_order_message(no_number))


if __name__ == "__main__":
    unittest.main()
