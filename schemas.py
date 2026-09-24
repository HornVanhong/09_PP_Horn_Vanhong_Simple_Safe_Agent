from typing import List, Dict, Any
from pydantic import BaseModel, Field


# Tool input models
class SearchProductsInput(BaseModel):
    query: str = Field(..., min_length=1, description="Keyword or category to search")


class CheckStockInput(BaseModel):
    product_id: int = Field(..., gt=0, description="Product ID to check stock for")


class DeleteProductInput(BaseModel):
    product_id: int = Field(..., gt=0, description="Product ID to delete")


# Tool definitions for OpenAI function calling
TOOLS_SPEC: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search products by keyword or category name",
            "parameters": SearchProductsInput.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Check stock quantity for a product ID",
            "parameters": CheckStockInput.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_product",
            "description": "Delete a product from the catalog (Admin only)",
            "parameters": DeleteProductInput.model_json_schema()
        }
    }
]
