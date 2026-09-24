"""
schemas.py
Explicit tool input/output schemas using Pydantic.
Defines parameter types, constraints, and descriptions for agent tool calling.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class SearchProductsInput(BaseModel):
    """Schema for searching products by keyword or category."""
    query: str = Field(
        ...,
        min_length=1,
        description="The search keyword or category (e.g., 'laptop', 'mouse', 'accessory')."
    )


class CheckStockInput(BaseModel):
    """Schema for checking stock of a product by ID."""
    product_id: int = Field(
        ...,
        gt=0,
        description="The unique positive integer ID of the product."
    )


class DeleteProductInput(BaseModel):
    """Schema for deleting a product from inventory (Admin action)."""
    product_id: int = Field(
        ...,
        gt=0,
        description="The unique positive integer ID of the product to delete permanently."
    )


# OpenAI Function Calling format specification
TOOLS_SPEC: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search the product catalog by keyword or category.",
            "parameters": SearchProductsInput.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Check the available stock quantity and details for a specific product ID.",
            "parameters": CheckStockInput.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_product",
            "description": "Delete a product permanently from the catalog (Admin only).",
            "parameters": DeleteProductInput.model_json_schema()
        }
    }
]
