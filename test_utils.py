import unittest

import utils


class UtilsTests(unittest.TestCase):
    def test_extract_email_anywhere(self):
        message = "Hello, contact me at middle.user@example.com for details."
        self.assertEqual(utils.extract_email(message), "middle.user@example.com")
        self.assertTrue(utils.contains_email(message))

    def test_contains_email_false_when_absent(self):
        self.assertFalse(utils.contains_email("just words and numbers 1234"))

    def test_cp_amount_is_largest_number(self):
        message = "small 4 big 42 bigger 105 and smallest 1"
        self.assertEqual(utils.cp_amount(message), 105.0)

    def test_order_rule_three_lines_email_and_number(self):
        valid = "TypeA\nDetails line\ncustomer@example.com\nAmount 50"
        self.assertTrue(utils.is_order(valid))

        missing_lines = "TypeA\ncustomer@example.com"
        self.assertFalse(utils.is_order(missing_lines))

        no_email = "TypeA\nNotes\nNo email here\nAmount 50"
        self.assertFalse(utils.is_order(no_email))

    def test_route_orders_last_write_wins_by_type_and_amount(self):
        messages = [
            "TypeA\nInfo\nfirst@example.com\nAmount 10",
            "TypeA\nInfo updated\nsecond@example.com\nAmount 10",  # same key, should replace
            "TypeB\nOther\nthird@example.com\nAmount 20",
        ]

        routed = utils.route_orders(messages)
        self.assertEqual(len(routed), 2)

        key_a = ("TypeA", 10.0)
        key_b = ("TypeB", 20.0)

        self.assertIn(key_a, routed)
        self.assertIn(key_b, routed)
        self.assertEqual(routed[key_a]["email"], "second@example.com")
        self.assertEqual(routed[key_a]["raw"], messages[1])
        self.assertEqual(routed[key_b]["email"], "third@example.com")


if __name__ == "__main__":
    unittest.main()
