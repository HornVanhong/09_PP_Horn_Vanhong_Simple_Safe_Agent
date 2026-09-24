# Topic 07: Simple Safe Agent

Autonomous Store Assistant Agent with Tool Integration, Application-Level Permission Control, and Safety Harness.

---

## 1. Project Overview

The **Simple Safe Agent** is an autonomous assistant built for a retail/store management system. It can receive natural language requests from users, determine if external capabilities (tools) are required, generate structured tool invocations, and observe execution results to synthesize an accurate final response.

To ensure safety and security, the application enforces the core principle:
> **The model proposes an action. The application decides whether that action is allowed to execute.**

---

## 2. Available Tools

The application implements three concrete tools with defined input schemas:

| Tool Name | Input Schema | Description |
|---|---|---|
| `search_products` | `query: str` (min length: 1) | Searches catalog items matching a keyword or category. |
| `check_stock` | `product_id: int` ($>0$) | Checks stock quantity and availability for a specific product ID. |
| `delete_product` | `product_id: int` ($>0$) | Permanently removes an item from catalog (Admin action). |

---

## 3. Agent Loop

The agent demonstrates the autonomous decision-action-observation cycle:

```
User Request
     │
     ▼
┌──────────────┐
│  Agent / LLM │ ◄───────────────────────────────────┐
└──────┬───────┘                                     │
       │ Proposes tool call with arguments           │ Tool Result
       ▼                                             │ or Controlled Error
┌──────────────┐                                     │
│ Safety       │ Checks:                             │
│ Harness      │ 1. Role Permission (RBAC)           │
│ (Gatekeeper) │ 2. Pydantic Input Validation        │
└──────┬───────┘                                     │
       │ If Authorized & Valid                       │
       ▼                                             │
┌──────────────┐                                     │
│   Tools.py   ├─────────────────────────────────────┘
└──────────────┘
```

When no further tool calls are needed or the goal is satisfied, the LLM produces the final answer to the user.

---

## 4. Permission Rule (Role-Based Access Control)

Permissions are strictly validated in **application code** (`harness.py`), never delegated solely to model prompts:

| Action / Tool | Customer Role | Admin Role | Enforced In |
|---|:---:|:---:|:---:|
| `search_products` | Allowed (✓) | Allowed (✓) | `SafetyHarness.check_permission` |
| `check_stock` | Allowed (✓) | Allowed (✓) | `SafetyHarness.check_permission` |
| `delete_product` | **Denied (✗)** | **Allowed (✓)** | `SafetyHarness.check_permission` |

If an unauthorized role attempts to call a restricted tool, the harness immediately returns a controlled `PERMISSION_DENIED` error without executing the underlying function.

---

## 5. Safety Controls

1. **Input Validation (Pydantic Schemas)**:
   - Tool parameters are validated against strict types (e.g. `product_id` must be an integer $> 0$, search query cannot be empty).
   - Prevents invalid values or malicious injection.

2. **Controlled Error Handling**:
   - The application traps exceptions and returns structured JSON error payloads (`PERMISSION_DENIED`, `VALIDATION_FAILED`, `NOT_FOUND`).
   - Allows the LLM to inspect errors and explain issues politely to the user instead of crashing the system.

3. **Maximum Iteration Limit**:
   - The loop enforces `max_iterations` (default: 5) to guard against infinite loops or excessive API consumption.

---

## 6. How to Run & Example Run

### Setup Instructions

1. **Clone repository and navigate to project**:
   ```bash
   cd "Safe Agent"
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up API Key**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and insert your OpenAI API key.

5. **Run Automated Test Suite (No API Key Required)**:
   ```bash
   python -m unittest discover tests
   ```

6. **Start the Application**:
   ```bash
   python main.py
   ```

---

### Example Traces

#### Example 1: Multi-Step Customer Query (Success)
- **Role**: `Customer`
- **Request**: *"Find a laptop and check if it is currently in stock."*
```text
[AGENT START] Role: 'customer' | Max Iterations: 5
[USER PROMPT]: Find a laptop and check if it is currently in stock.

--- Iteration 1/5 ---
[ACTION PROPOSED] Tool: 'search_products' | Args: {'query': 'laptop'}
[OBSERVATION] Result: {'status': 'success', 'count': 1, 'results': [{'id': 1, 'name': 'Dell XPS 15 Laptop', 'category': 'laptop', 'price': 1500.0}]}

--- Iteration 2/5 ---
[ACTION PROPOSED] Tool: 'check_stock' | Args: {'product_id': 1}
[OBSERVATION] Result: {'status': 'success', 'product_id': 1, 'name': 'Dell XPS 15 Laptop', 'stock': 4, 'in_stock': True}

--- Iteration 3/5 ---
[DECISION] Final answer reached.

[FINAL RESPONSE]:
We found the Dell XPS 15 Laptop (ID: 1), priced at $1,500.00. It is currently in stock with 4 units available.
```

#### Example 2: Permission Control Enforced (Blocked Customer)
- **Role**: `Customer`
- **Request**: *"Please delete product with ID 1."*
```text
[AGENT START] Role: 'customer' | Max Iterations: 5
[USER PROMPT]: Please delete product with ID 1.

--- Iteration 1/5 ---
[ACTION PROPOSED] Tool: 'delete_product' | Args: {'product_id': 1}
[OBSERVATION] Result: {'status': 'error', 'error_type': 'PERMISSION_DENIED', 'message': "PERMISSION_DENIED: Role 'customer' is not authorized to execute tool 'delete_product'."}

--- Iteration 2/5 ---
[DECISION] Final answer reached.

[FINAL RESPONSE]:
I apologize, but as a customer, you do not have permission to delete products from the catalog. This action is restricted to administrators.
```
