"""Command-line entry point for the teaching lab."""
import argparse
import os
from .graph import build_graph, run_ticket

def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LangGraph support triage lesson")
    parser.add_argument("--ticket", required=True, help="Support ticket text")
    parser.add_argument("--thread", default="cli-demo", help="Checkpoint thread id")
    parser.add_argument("--real", action="store_true", help="Use the server-side OpenAI key from the CRM .env")
    args = parser.parse_args()
    if args.real:
        os.environ["LANGGRAPH_USE_OPENAI"] = "true"
    result = run_ticket(build_graph(), args.ticket, args.thread)
    print(f"\nFinal reply:\n{result['final_reply']}")
    print(f"\nTrace: {' -> '.join(result['events'])}")

if __name__ == "__main__":
    main()
