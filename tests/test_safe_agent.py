import unittest
from schemas import SearchProductsInput, CheckStockInput, DeleteProductInput, TOOLS_SPEC
from harness import SafetyHarness
import tools


class TestSafeAgentComponents(unittest.TestCase):

    def setUp(self):
        # Reset database before each test
        tools._save_data(list(tools.DEFAULT_PRODUCTS))

    def test_tool_schemas_valid(self):
        search = SearchProductsInput(query="laptop")
        self.assertEqual(search.query, "laptop")

        stock = CheckStockInput(product_id=1)
        self.assertEqual(stock.product_id, 1)

        del_input = DeleteProductInput(product_id=2)
        self.assertEqual(del_input.product_id, 2)

    def test_tool_schemas_invalid_constraints(self):
        with self.assertRaises(Exception):
            CheckStockInput(product_id=0)

        with self.assertRaises(Exception):
            CheckStockInput(product_id=-5)

        with self.assertRaises(Exception):
            SearchProductsInput(query="")

    def test_tool_search_products(self):
        res = tools.search_products(query="laptop")
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["count"], 1)
        self.assertIn("Dell", res["results"][0]["name"])

    def test_tool_check_stock(self):
        res = tools.check_stock(product_id=1)
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["in_stock"])
        self.assertEqual(res["stock"], 4)

        not_found = tools.check_stock(product_id=9999)
        self.assertEqual(not_found["status"], "error")
        self.assertEqual(not_found["error_type"], "NOT_FOUND")

    def test_customer_cannot_delete_product(self):
        harness = SafetyHarness(user_role="customer")

        can_search, _ = harness.check_permission("search_products")
        self.assertTrue(can_search)

        can_check, _ = harness.check_permission("check_stock")
        self.assertTrue(can_check)

        can_delete, msg = harness.check_permission("delete_product")
        self.assertFalse(can_delete)
        self.assertIn("PERMISSION_DENIED", msg)

        res = harness.execute_tool_safely("delete_product", {"product_id": 1})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error_type"], "PERMISSION_DENIED")

    def test_admin_can_delete_product(self):
        harness = SafetyHarness(user_role="admin")

        can_delete, _ = harness.check_permission("delete_product")
        self.assertTrue(can_delete)

        res = harness.execute_tool_safely("delete_product", {"product_id": 3})
        self.assertEqual(res["status"], "success")

    def test_input_validation_negative_id(self):
        harness = SafetyHarness(user_role="customer")

        res = harness.execute_tool_safely("check_stock", {"product_id": -10})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error_type"], "VALIDATION_FAILED")


if __name__ == "__main__":
    unittest.main()
