import sys
import argparse
from agent import SafeAgent


def parse_args():
    parser = argparse.ArgumentParser(description="Simple Safe Agent CLI")
    parser.add_argument(
        "--role",
        choices=["customer", "admin"],
        default=None,
        help="User role (customer or admin)"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Prompt to run directly"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in offline simulation mode"
    )
    return parser.parse_args()


def interactive_mode(mock_flag: bool = False):
    print("=" * 60)
    print("      Topic 07: Simple Safe Agent Application")
    print("=" * 60)
    print("\nSelect User Role:")
    print("  1) Customer (Default: can search products & check stock)")
    print("  2) Admin    (Authorized: can search, check stock & delete products)")
    role_choice = input("Enter choice [1/2, default 1]: ").strip()
    role = "admin" if role_choice == "2" else "customer"

    agent = SafeAgent(user_role=role, mock_mode=mock_flag)

    mode_name = "SIMULATION (No API Key Required)" if agent.mock_mode else f"LIVE LLM ({agent.model})"
    print(f"\n[INIT] Active Role: [{role.upper()}] | Engine: {mode_name}")
    print("Type 'exit' or 'quit' to terminate the session.\n")

    while True:
        try:
            prompt = input(f"[{role}] Enter request > ").strip()
            if not prompt:
                continue
            if prompt.lower() in ["exit", "quit", "q"]:
                print("Exiting Simple Safe Agent. Goodbye!")
                break

            answer = agent.run(prompt)
            print("\n[FINAL RESPONSE]:")
            print(answer)
            print("-" * 60 + "\n")
        except KeyboardInterrupt:
            print("\nSession interrupted. Exiting...")
            break


def main():
    args = parse_args()

    if args.prompt:
        role = args.role or "customer"
        agent = SafeAgent(user_role=role, mock_mode=args.mock)
        print(f"Running execution with Role: [{role.upper()}] | Engine: {'SIMULATION' if agent.mock_mode else 'LIVE'}")
        answer = agent.run(args.prompt)
        print("\n[FINAL RESPONSE]:")
        print(answer)
    else:
        interactive_mode(mock_flag=args.mock)


if __name__ == "__main__":
    main()
