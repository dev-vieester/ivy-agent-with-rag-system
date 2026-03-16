# agents/ivy_agent.py

from dotenv import load_dotenv
load_dotenv()

from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from tools.lc_tools import ALL_LC_TOOLS


# ── Model ─────────────────────────────────────────────────────────────────────

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    max_tokens=4096,
)


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Ivy, an intelligent assistant for this company.

You have access to two knowledge sources:
1. Internal company documents — use `search_company_docs` for anything about company
   policies, reports, employees, finances, or internal data.
2. The internet — use `web_search` for current events, external facts, or anything
   not in internal documents.

You also have tools to process and deliver information:
- CSV tools: preview, filter, analyze, and export CSV data
- `summarize_and_export`: produce PDF/DOCX/TXT reports from any content
- `send_email`: send emails with optional file attachments
- `add_reminder`, `list_reminders`, `cancel_reminder`: schedule and manage reminders

Chaining tools is encouraged. Examples:
- "Summarize the Q3 report and email it" → search_company_docs → summarize_and_export → send_email
- "Analyse sales.csv and send me a PDF" → csv_export_analysis → send_email
- "Remind me to review the compliance docs tomorrow" → search_company_docs → add_reminder

For company-specific questions always prefer search_company_docs over web_search.
"""


# ── Agent ─────────────────────────────────────────────────────────────────────

agent = create_agent(
    model=llm,
    tools=ALL_LC_TOOLS,
    system_prompt=SYSTEM_PROMPT,
    name="ivy_agent",
)


# ── IvyAgent wrapper ──────────────────────────────────────────────────────────

class IvyAgent:
    def __init__(self):
        self.agent = agent
        self.chat_history: list = []

    def run(self, user_message: str) -> str:
        result = self.agent.invoke({
            "messages": self.chat_history + [
                HumanMessage(content=user_message)
            ]
        })

        all_messages = result["messages"]
        last_ai = next(
            (m for m in reversed(all_messages) if isinstance(m, AIMessage)),
            None
        )

        # Fix: handle both string and list content blocks
        if last_ai is None:
            answer = "No response."
        elif isinstance(last_ai.content, str):
            answer = last_ai.content
        elif isinstance(last_ai.content, list):
            # Extract text from content blocks
            answer = " ".join(
                block["text"] if isinstance(block, dict) else block.text
                for block in last_ai.content
                if (isinstance(block, dict) and block.get("type") == "text")
                or (hasattr(block, "type") and block.type == "text")
            )
        else:
            answer = str(last_ai.content)

        # Persist history
        self.chat_history.append(HumanMessage(content=user_message))
        self.chat_history.append(AIMessage(content=answer))

        return answer

    def stream(self, user_message: str):
        """
        Stream intermediate steps back to the caller.
        Yields (event_type, content) tuples as the agent works.
        """
        for chunk in self.agent.stream(
            {"messages": self.chat_history + [HumanMessage(content=user_message)]},
            stream_mode="values",
        ):
            latest = chunk["messages"][-1]

            if isinstance(latest, AIMessage):
                if latest.tool_calls:
                    tool_names = [tc["name"] for tc in latest.tool_calls]
                    yield ("tool_call", f"Calling: {', '.join(tool_names)}")
                elif latest.content:
                    yield ("answer", latest.content)
            # tool result messages are ToolMessage instances — skip or surface
            # them here if you want to show "got result from X" in your UI

        # After streaming, persist the final answer to history
        final = self.agent.invoke({
            "messages": self.chat_history + [HumanMessage(content=user_message)]
        })
        all_messages = final["messages"]
        last_ai = next(
            (m for m in reversed(all_messages) if isinstance(m, AIMessage)),
            None
        )
        if last_ai:
            self.chat_history.append(HumanMessage(content=user_message))
            self.chat_history.append(AIMessage(content=last_ai.content))

    def reset(self):
        """Clear conversation history."""
        self.chat_history = []
        print("History cleared.")

    def chat(self):
        """Terminal chat loop."""
        print("Ivy is ready. Commands: 'exit' to quit, 'reset' to clear history.\n")
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Goodbye.")
                break
            if user_input.lower() == "reset":
                self.reset()
                continue

            response = self.run(user_input)
            print(f"\nIvy: {response}\n")