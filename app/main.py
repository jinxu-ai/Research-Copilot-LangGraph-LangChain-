# app/main.py
"""
Project entrypoint for the minimal Agent flow (Step 3).
- Reads a question from CLI (argument) or interactive prompt.
- Calls the minimal DeepSeek conversation chain.
- Prints the model's answer.

Run:
    python app/main.py --q "What is LangGraph in one sentence?"

Or interactive:
    python app/main.py
"""

import argparse
from chains.deepseek_chain import ask


def main():
    """
    CLI entrypoint.
    If --q is provided, answer once; otherwise enter a single-turn interactive prompt.
    """
    parser = argparse.ArgumentParser(description="Minimal DeepSeek chat entrypoint.")
    parser.add_argument("--q", "--question", dest="question", type=str, help="Your question")
    parser.add_argument("--temp", dest="temperature", type=float, default=0.0, help="Sampling temperature")
    parser.add_argument(
        "--system",
        dest="system_prompt",
        type=str,
        default="You are a helpful research copilot. Be concise and accurate.",
        help="Optional system instruction"
    )
    args = parser.parse_args()

    if args.question:
        reply = ask(args.question, system_prompt=args.system_prompt, temperature=args.temperature)
        print("\n🤖", reply)
    else:
        try:
            user = input("💬 Your question: ").strip()
            if not user:
                print("No input. Exit.")
                return
            reply = ask(user, system_prompt=args.system_prompt, temperature=args.temperature)
            print("\n🤖", reply)
        except KeyboardInterrupt:
            print("\nExit.")


if __name__ == "__main__":
    main()
