"""
harness.py
Safety Harness and Control Layer.
Handles:
- Application-level permission checks (Role-Based Access Control)
- Input safety validation using Pydantic schemas
- Structured error handling and failure boundaries
"""

from typing import Tuple, Dict, Any
from pydantic import ValidationError

from schemas import SearchProductsInput, CheckStockInput, DeleteProductInput
import tools

# Role-Based Access Control (RBAC) Matrix
# Checked in application code, NOT just in the model prompt
ROLE_PERMISSIONS: Dict[str, list] = {
    "customer": ["search_products", "check_stock"],
    "admin": ["search_products", "check_stock", "delete_product"]
}

# Mapping tool names to Pydantic input schemas
TOOL_SCHEMAS = {
    "search_products": SearchProductsInput,
    "check_stock": CheckStockInput,
    "delete_product": DeleteProductInput
}

# Mapping tool names to callable Python functions
TOOL_FUNCTIONS = {
    "search_products": tools.search_products,
    "check_stock": tools.check_stock,
    "delete_product": tools.delete_product
}


class SafetyHarness:
    """Safety Harness that acts as the application-level gatekeeper."""

    def __init__(self, user_role: str = "customer"):
        self.user_role = user_role.strip().lower()

    def check_permission(self, tool_name: str) -> Tuple[bool, str]:
        """Verify whether the current role is authorized to execute the requested tool."""
        allowed_tools = ROLE_PERMISSIONS.get(self.user_role, [])
        if tool_name not in allowed_tools:
            return False, f"PERMISSION_DENIED: Role '{self.user_role}' is not authorized to execute tool '{tool_name}'."
        return True, "Authorized"

    def validate_inputs(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, Any]:
        """Validate input arguments using Pydantic schemas before calling the function."""
        schema = TOOL_SCHEMAS.get(tool_name)
        if not schema:
            return False, f"UNKNOWN_TOOL: Tool '{tool_name}' has no defined schema."
        try:
            validated_model = schema(**arguments)
            return True, validated_model.model_dump()
        except ValidationError as e:
            return False, f"VALIDATION_FAILED: {e.errors()}"

    def execute_tool_safely(self, tool_name: str, raw_arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the three-phase safety pipeline:
        1. Permission Verification (RBAC)
        2. Input Schema Validation
        3. Exception-bounded Execution
        """
        # Phase 1: Permission Check
        is_allowed, perm_msg = self.check_permission(tool_name)
        if not is_allowed:
            return {
                "status": "error",
                "error_type": "PERMISSION_DENIED",
                "message": perm_msg
            }

        # Phase 2: Input Validation
        is_valid, validated_args_or_err = self.validate_inputs(tool_name, raw_arguments)
        if not is_valid:
            return {
                "status": "error",
                "error_type": "VALIDATION_FAILED",
                "message": validated_args_or_err
            }

        # Phase 3: Safe Function Execution
        func = TOOL_FUNCTIONS.get(tool_name)
        if not func:
            return {
                "status": "error",
                "error_type": "UNKNOWN_TOOL",
                "message": f"No implementation found for tool '{tool_name}'."
            }

        try:
            result = func(**validated_args_or_err)
            return result
        except Exception as ex:
            return {
                "status": "error",
                "error_type": "EXECUTION_EXCEPTION",
                "message": f"Execution error in tool '{tool_name}': {str(ex)}"
            }
