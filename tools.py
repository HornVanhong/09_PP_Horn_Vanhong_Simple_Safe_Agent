import json
import os
from typing import Dict, Any, List

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "products.json")

DEFAULT_PRODUCTS = [
    {
        "id": 1,
        "name": "Dell XPS 15 Laptop",
        "category": "laptop",
        "price": 1500.0,
        "stock": 4
    },
    {
        "id": 2,
        "name": "Logitech MX Master 3S Mouse",
        "category": "accessory",
        "price": 99.0,
        "stock": 0
    },
    {
        "id": 3,
        "name": "Mechanical Keyboard RGB",
        "category": "accessory",
        "price": 120.0,
        "stock": 12
    }
]


def _load_data() -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_FILE):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        _save_data(DEFAULT_PRODUCTS)
        return list(DEFAULT_PRODUCTS)
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return list(DEFAULT_PRODUCTS)


def _save_data(data: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def search_products(query: str) -> Dict[str, Any]:
    products = _load_data()
    q = query.lower()
    matches = [
        {
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "price": p["price"]
        }
        for p in products
        if q in p["name"].lower() or q in p["category"].lower()
    ]
    return {
        "status": "success",
        "count": len(matches),
        "results": matches
    }


def check_stock(product_id: int) -> Dict[str, Any]:
    products = _load_data()
    for p in products:
        if p["id"] == product_id:
            return {
                "status": "success",
                "product_id": product_id,
                "name": p["name"],
                "stock": p["stock"],
                "in_stock": p["stock"] > 0
            }
    return {
        "status": "error",
        "error_type": "NOT_FOUND",
        "message": f"Product with ID {product_id} not found."
    }


def delete_product(product_id: int) -> Dict[str, Any]:
    products = _load_data()
    initial_len = len(products)
    products = [p for p in products if p["id"] != product_id]

    if len(products) == initial_len:
        return {
            "status": "error",
            "error_type": "NOT_FOUND",
            "message": f"Product with ID {product_id} does not exist."
        }

    _save_data(products)
    return {
        "status": "success",
        "message": f"Product {product_id} successfully deleted from the catalog."
    }
