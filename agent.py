"""Terminal version. Run with: py agent.py"""
from getpass import getpass
from pathlib import Path
from openai import OpenAI
from agent_core import AgentState, run_turn, friendly_error


def main():
    client = OpenAI(api_key=getpass("Enter your OpenAI API key: "), timeout=30, max_retries=0)
    state = AgentState()
    folder = Path(__file__).resolve().parent / "notes"
    exported = set()
    while True:
        goal = input("What should the agent do? (exit/new): ").strip()
        if goal.lower() == "exit":
            print("Goodbye!")
            break
        if goal.lower() == "new":
            state = AgentState()
            print("New conversation started.")
            continue
        if not goal:
            print("Please enter a message.")
            continue
        try:
            print("Thinking...")
            reply = run_turn(client, goal, state)
            for event in reply.events:
                print("Tool result:", event["result"])
            print("\nAI response:", reply.text)
            print("Model used:", reply.model)
        except Exception as error:
            print(friendly_error(error))
            state.last_response_id = None
        # Export even if a follow-up API call fails after a successful save.
        for note in state.notes:
            if note["filename"] not in exported:
                try:
                    folder.mkdir(exist_ok=True)
                    with (folder / note["filename"]).open("x", encoding="utf-8") as file:
                        file.write(note["content"])
                    exported.add(note["filename"])
                    print("Written to notes/" + note["filename"])
                except OSError:
                    print("Could not write the local note file. Check folder permissions.")


if __name__ == "__main__":
    main()
