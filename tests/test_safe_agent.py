"""
test_safe_agent.py
Automated unit and integration tests verifying the homework requirements:
1. Tool Schemas & Input Validation (Requirement 2B & 2D)
2. Tool Implementations (Requirement 2B)
3. Application-level Permission Control / RBAC (Requirement 2C)
4. Safety Harness Gatekeeping & Controlled Errors (Requirement 2D)
"""

import unittest
from schemas import SearchProductsInput, CheckStockInput, DeleteProductInput, TOOLS_SPEC
from harness import SafetyHarness
import tools


class TestSafeAgentComponents(unittest.TestCase):

    def setUp(self):
        # Reset mock database before each test
        tools._save_data(list(tools.DEFAULT_PRODUCTS))

    def test_tool_schemas_valid(self):
        """Verify that valid inputs satisfy Pydantic schemas."""
        search = SearchProductsInput(query="laptop")
        self.assertEqual(search.query, "laptop")

        stock = CheckStockInput(product_id=1)
        self.assertEqual(stock.product_id, 1)

        del_input = DeleteProductInput(product_id=2)
        self.assertEqual(del_input.product_id, 2)

    def test_tool_schemas_invalid_constraints(self):
        """Verify that non-positive IDs violate schema constraints (Safety 2D)."""
        with self.assertRaises(Exception):
            CheckStockInput(product_id=0)

        with self.assertRaises(Exception):
            CheckStockInput(product_id=-5)

        with self.assertRaises(Exception):
            SearchProductsInput(query="")

    def test_tool_search_products(self):
        """Verify search_products tool returns expected items."""
        res = tools.search_products(query="laptop")
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["count"], 1)
        self.assertIn("Dell", res["results"][0]["name"])

    def test_tool_check_stock(self):
        """Verify check_stock tool returns stock info or not found."""
        res = tools.check_stock(product_id=1)
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["in_stock"])
        self.assertEqual(res["stock"], 4)

        not_found = tools.check_stock(product_id=9999)
        self.assertEqual(not_found["status"], "error")
        self.assertEqual(not_found["error_type"], "NOT_FOUND")

    def test_customer_permission_blocked_on_sensitive_action(self):
        """Verify that Customer role is denied from executing delete_product (Requirement 2C)."""
        harness = SafetyHarness(user_role="customer")
        
        # Customer should be allowed to search and check stock
        can_search, _ = harness.check_permission("search_products")
        self.assertTrue(can_search)

        can_check, _ = harness.check_permission("check_stock")
        self.assertTrue(can_check)

        # Customer must be BLOCKED from deleting products
        can_delete, msg = harness.check_permission("delete_product")
        self.assertFalse(can_delete)
        self.assertIn("PERMISSION_DENIED", msg)

        # Calling execute_tool_safely must return controlled error
        exec_res = harness.execute_tool_safely("delete_product", {"product_id": 1})
        self.assertEqual(exec_res["status"], "error")
        self.assertEqual(exec_res["error_type"], "PERMISSION_DENIED")

    def test_admin_permission_allowed_on_sensitive_action(self):
        """Verify that Admin role is authorized to execute delete_product (Requirement 2C)."""
        harness = SafetyHarness(user_role="admin")
        
        can_delete, _ = harness.check_permission("delete_product")
        self.assertTrue(can_delete)

        # Execute safe deletion
        exec_res = harness.execute_tool_safely("delete_product", {"product_id": 3})
        self.assertEqual(exec_res["status"], "success")

    def test_safety_harness_validation_guard(self):
        """Verify that invalid parameters are rejected before execution (Requirement 2D)."""
        harness = SafetyHarness(user_role="customer")
        
        # Negative product ID should fail validation
        res = harness.execute_tool_safely("check_stock", {"product_id": -10})
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error_type"], "VALIDATION_FAILED")


if __name__ == "__main__":
    unittest.main()
