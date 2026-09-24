import os
import json
import re
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from schemas import TOOLS_SPEC
from harness import SafetyHarness

load_dotenv()


class SafeAgent:
    def __init__(
        self,
        user_role: str = "customer",
        max_iterations: int = 5,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        mock_mode: bool = False
    ):
        self.user_role = user_role.strip().lower()
        self.max_iterations = int(os.getenv("MAX_AGENT_ITERATIONS", max_iterations))
        self.model = model or os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.harness = SafetyHarness(user_role=self.user_role)
        self.mock_mode = mock_mode

        # If no API key is set, default to simulation mode for local testing
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.mock_mode or not resolved_key or resolved_key.strip() in ["", "your_openai_api_key_here"]:
            self.client = None
            self.mock_mode = True
        else:
            try:
                from openai import OpenAI
                kwargs = {"api_key": resolved_key}
                if base_url or os.getenv("OPENAI_BASE_URL"):
                    kwargs["base_url"] = base_url or os.getenv("OPENAI_BASE_URL")
                self.client = OpenAI(**kwargs)
            except Exception:
                self.client = None
                self.mock_mode = True

    def run(self, user_prompt: str) -> str:
        if self.mock_mode:
            return self._run_mock_loop(user_prompt)
        return self._run_live_loop(user_prompt)

    def _run_live_loop(self, user_prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a helpful Store Assistant. The user's role is '{self.user_role}'.\n"
                    "Use available tools when necessary to fulfill user requests.\n"
                    "If a tool call returns an error or permission denied, explain it politely to the user.\n"
                    "Do not assume tool results; only report data returned by the tools."
                )
            },
            {"role": "user", "content": user_prompt}
        ]

        iteration = 0
        print(f"\n[AGENT START] Mode: LIVE (LLM: {self.model}) | Role: '{self.user_role}' | Max Iterations: {self.max_iterations}")
        print(f"[USER PROMPT]: {user_prompt}")

        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOLS_SPEC,
                    tool_choice="auto"
                )
            except Exception as e:
                return f"[API ERROR] Error communicating with LLM provider: {str(e)}"

            response_message = response.choices[0].message
            messages.append(response_message)

            if not response_message.tool_calls:
                print("[DECISION] Final answer reached.")
                return response_message.content or ""

            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                print(f"[ACTION PROPOSED] Tool: '{tool_name}' | Args: {args}")

                # Call safety harness
                tool_result = self.harness.execute_tool_safely(tool_name, args)
                print(f"[OBSERVATION] Result: {tool_result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result)
                })

        limit_msg = (
            f"[SAFETY LIMIT] Maximum iteration limit ({self.max_iterations}) reached. "
            "Halting loop to prevent an endless cycle."
        )
        print(limit_msg)
        return limit_msg

    def _run_mock_loop(self, user_prompt: str) -> str:
        """Simulation mode to test the agent loop offline."""
        print(f"\n[AGENT START] Mode: SIMULATION / DEMO | Role: '{self.user_role}' | Max Iterations: {self.max_iterations}")
        print(f"[USER PROMPT]: {user_prompt}")

        prompt_lower = user_prompt.lower()
        iteration = 0

        # Delete product
        if "delete" in prompt_lower or "remove" in prompt_lower:
            match = re.search(r"(\d+)", user_prompt)
            prod_id = int(match.group(1)) if match else 1

            iteration += 1
            print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
            print(f"[ACTION PROPOSED] Tool: 'delete_product' | Args: {{'product_id': {prod_id}}}")
            obs = self.harness.execute_tool_safely("delete_product", {"product_id": prod_id})
            print(f"[OBSERVATION] Result: {obs}")

            iteration += 1
            print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
            print("[DECISION] Final answer reached.")
            if obs.get("error_type") == "PERMISSION_DENIED":
                return (
                    f"I apologize, but as a '{self.user_role}', you do not have permission to delete "
                    "products from the catalog. This action is restricted to administrators."
                )
            elif obs.get("status") == "success":
                return f"Product ID {prod_id} was successfully deleted from the store catalog."
            else:
                return f"Could not delete product: {obs.get('message')}"

        # Invalid/negative product ID
        elif re.search(r"-\d+", user_prompt) or "id 0" in prompt_lower or "id: 0" in prompt_lower:
            match = re.search(r"(-\d+)", user_prompt)
            invalid_id = int(match.group(1)) if match else -1
            iteration += 1
            print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
            print(f"[ACTION PROPOSED] Tool: 'check_stock' | Args: {{'product_id': {invalid_id}}}")
            obs = self.harness.execute_tool_safely("check_stock", {"product_id": invalid_id})
            print(f"[OBSERVATION] Result: {obs}")

            iteration += 1
            print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
            print("[DECISION] Final answer reached.")
            return f"Input validation rejected the request: Product ID must be a positive integer greater than 0. Harness error: {obs.get('message')}"

        # Search and check stock
        elif "find" in prompt_lower or "search" in prompt_lower or "check" in prompt_lower or "laptop" in prompt_lower or "mouse" in prompt_lower:
            keyword = "laptop" if "laptop" in prompt_lower else ("mouse" if "mouse" in prompt_lower else "accessory")

            iteration += 1
            print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
            print(f"[ACTION PROPOSED] Tool: 'search_products' | Args: {{'query': '{keyword}'}}")
            search_obs = self.harness.execute_tool_safely("search_products", {"query": keyword})
            print(f"[OBSERVATION] Result: {search_obs}")

            if "stock" in prompt_lower or "check" in prompt_lower or search_obs.get("results"):
                found_id = search_obs["results"][0]["id"] if search_obs.get("results") else 1

                iteration += 1
                print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
                print(f"[ACTION PROPOSED] Tool: 'check_stock' | Args: {{'product_id': {found_id}}}")
                stock_obs = self.harness.execute_tool_safely("check_stock", {"product_id": found_id})
                print(f"[OBSERVATION] Result: {stock_obs}")

                iteration += 1
                print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
                print("[DECISION] Final answer reached.")
                name = stock_obs.get("name", "Product")
                units = stock_obs.get("stock", 0)
                status_str = "in stock" if stock_obs.get("in_stock") else "out of stock"
                return f"We found the {name} (ID: {found_id}). It is currently {status_str} with {units} units available."

            iteration += 1
            print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
            print("[DECISION] Final answer reached.")
            return f"Found {search_obs.get('count', 0)} product(s): {search_obs.get('results')}"

        # Default fallback
        iteration += 1
        print(f"\n--- Iteration {iteration}/{self.max_iterations} ---")
        print("[DECISION] Final answer reached directly (no tools needed).")
        return (
            "I am your Simple Safe Store Assistant. You can ask me to search for products "
            "(e.g., 'Find a laptop and check stock') or manage items if you have admin privileges."
        )
