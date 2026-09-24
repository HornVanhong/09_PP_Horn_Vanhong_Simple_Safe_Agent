from typing import Tuple, Dict, Any
from pydantic import ValidationError

from schemas import SearchProductsInput, CheckStockInput, DeleteProductInput
import tools

# Role permissions
ROLE_PERMISSIONS: Dict[str, list] = {
    "customer": ["search_products", "check_stock"],
    "admin": ["search_products", "check_stock", "delete_product"]
}

# Map tool names to schemas
TOOL_SCHEMAS = {
    "search_products": SearchProductsInput,
    "check_stock": CheckStockInput,
    "delete_product": DeleteProductInput
}

# Map tool names to functions
TOOL_FUNCTIONS = {
    "search_products": tools.search_products,
    "check_stock": tools.check_stock,
    "delete_product": tools.delete_product
}


class SafetyHarness:
    def __init__(self, user_role: str = "customer"):
        self.user_role = user_role.strip().lower()

    def check_permission(self, tool_name: str) -> Tuple[bool, str]:
        allowed_tools = ROLE_PERMISSIONS.get(self.user_role, [])
        if tool_name not in allowed_tools:
            return False, f"PERMISSION_DENIED: Role '{self.user_role}' is not authorized to execute tool '{tool_name}'."
        return True, "Authorized"

    def validate_inputs(self, tool_name: str, arguments: Dict[str, Any]) -> Tuple[bool, Any]:
        schema = TOOL_SCHEMAS.get(tool_name)
        if not schema:
            return False, f"UNKNOWN_TOOL: Tool '{tool_name}' has no defined schema."
        try:
            validated = schema(**arguments)
            return True, validated.model_dump()
        except ValidationError as e:
            return False, f"VALIDATION_FAILED: {e.errors()}"

    def execute_tool_safely(self, tool_name: str, raw_arguments: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Check permission
        is_allowed, perm_msg = self.check_permission(tool_name)
        if not is_allowed:
            return {
                "status": "error",
                "error_type": "PERMISSION_DENIED",
                "message": perm_msg
            }

        # 2. Validate input arguments
        is_valid, validated_args_or_err = self.validate_inputs(tool_name, raw_arguments)
        if not is_valid:
            return {
                "status": "error",
                "error_type": "VALIDATION_FAILED",
                "message": validated_args_or_err
            }

        # 3. Run the tool
        func = TOOL_FUNCTIONS.get(tool_name)
        if not func:
            return {
                "status": "error",
                "error_type": "UNKNOWN_TOOL",
                "message": f"No implementation found for tool '{tool_name}'."
            }

        try:
            return func(**validated_args_or_err)
        except Exception as ex:
            return {
                "status": "error",
                "error_type": "EXECUTION_EXCEPTION",
                "message": f"Execution error in tool '{tool_name}': {str(ex)}"
            }
