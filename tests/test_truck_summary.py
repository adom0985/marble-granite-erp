import unittest
from server import calculate_truck_summary


class TruckSummaryTests(unittest.TestCase):
    def test_groups_same_material_across_widths(self):
        rows = [
            {"material_name": "صني 3 سم", "width": 1.0, "qty": 2, "area": 6.0, "price": 100},
            {"material_name": "صني 3 سم", "width": 1.5, "qty": 3, "area": 9.0, "price": 100},
            {"material_name": "صني 2 سم", "width": 1.0, "qty": 1, "area": 2.0, "price": 100},
        ]
        got = calculate_truck_summary(rows)
        self.assertEqual(len(got), 2)
        by_label = {x["material_label"]: x for x in got}
        self.assertEqual(by_label["صني 3 سم"]["total_qty"], 5)
        self.assertEqual(by_label["صني 3 سم"]["total_area"], 15.0)


if __name__ == "__main__":
    unittest.main()
