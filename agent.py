from pydantic import BaseModel, Field
import inspect
import asyncio
import os
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
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

# Load env
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("❌ GEMINI_API_KEY missing in .env file")


# --- Helper to wrap async -> sync ---
def async_tool(fn):
    # Inspect function signature
    sig = inspect.signature(fn)

    # Prepare annotations + defaults
    annotations = {}
    attrs = {}
    for name, param in sig.parameters.items():
        annotations[name] = str  # sab parameters string treat honge
        attrs[name] = Field(..., description=f"{name} parameter")

    # Create schema class dynamically
    ToolSchema = type(
        f"{fn.__name__.title()}Schema",
        (BaseModel,),
        {"__annotations__": annotations, **attrs},
    )

    async def _async_wrapper(**kwargs):
        return await fn(**kwargs)

    def _sync_wrapper(**kwargs):
        return asyncio.run(_async_wrapper(**kwargs))

    return StructuredTool(
        name=fn.__name__,
        description=fn.__doc__ or f"Tool for {fn.__name__}",
        func=_sync_wrapper,
        args_schema=ToolSchema,
    )


# ✅ Wrap async functions properly
tools = [
    async_tool(add_student),
    async_tool(get_student),
    async_tool(update_student),
    async_tool(delete_student),
    async_tool(list_students),
    async_tool(get_total_students),
    async_tool(get_students_by_department),
    async_tool(get_recent_onboarded_students),
    async_tool(get_active_students_last_7_days),
]

# Gemini model
model = ChatOpenAI(
    model="gemini-2.0-flash",
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# Create the agent
agent = create_react_agent(model, tools)


async def main():
    print("🤖 MongoDB Agent ready. Type your command (or 'exit'): ")
    while True:
        query = input("👉 ")
        if query.lower() in ["exit", "quit"]:
            break

        result = await agent.ainvoke({"messages": [("user", query)]})

        # ✅ Sirf last message ka content print karo
        if "messages" in result and len(result["messages"]) > 0:
            last_msg = result["messages"][-1]
            print("📌 Result:", last_msg.content.strip())
        else:
            print("📌 Result:", result)


if __name__ == "__main__":
    asyncio.run(main())
