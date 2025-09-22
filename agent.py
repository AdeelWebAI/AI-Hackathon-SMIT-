import asyncio
import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from tools import (
    add_student,
    get_student,
    update_student,
    delete_student,
    list_students,
    get_total_students,
    get_students_by_department,
    get_recent_onboarded_students,
    get_active_students_last_7_days,
)

# ---------------- Load ENV ----------------
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("❌ GEMINI_API_KEY missing in .env file")

# ---------------- Tools ----------------
# Directly use tools (they are already StructuredTool via @tool)
tools = [
    add_student,
    get_student,
    update_student,
    delete_student,
    list_students,
    get_total_students,
    get_students_by_department,
    get_recent_onboarded_students,
    get_active_students_last_7_days,
]

# ---------------- Model ----------------
model = ChatOpenAI(
    model="gemini-2.0-flash",
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# ---------------- Agent ----------------
agent = create_react_agent(model, tools)


async def main():
    print("🤖 MongoDB Agent ready. Type your command (or 'exit'): ")
    while True:
        query = input("👉 ")
        if query.lower() in ["exit", "quit"]:
            break

        result = await agent.ainvoke({"messages": [("user", query)]})

        # ✅ Print only the last assistant message
        if "messages" in result and len(result["messages"]) > 0:
            last_msg = result["messages"][-1]
            print("📌 Result:", last_msg.content.strip())
        else:
            print("📌 Result:", result)


if __name__ == "__main__":
    asyncio.run(main())
    