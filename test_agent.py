import asyncio
from agent import agent

async def main():
    print("🚀 Agent Test Started!")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break

        try:
            # ✅ Must pass both thread_id & checkpoint_ns
            result = await agent.ainvoke(
                {"messages": [("user", user_input)]},
                configurable={
                    "thread_id": "session-1",          # unique chat session
                    "checkpoint_ns": "students-agent"  # namespace for memory
                }
            )

            # Extract assistant's reply
            if "messages" in result and result["messages"]:
                response = result["messages"][-1].content
                print(f"Agent: {response}")
            else:
                print("⚠ No response from agent.")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
