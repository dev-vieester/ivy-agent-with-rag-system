from agents.ivy_agent import IvyAgent

agent = IvyAgent()

for event_type, content in agent.stream("Search the internet look for 3 fintech company in nigeria and the use xedlapay escrow prd, also using the report submit send the report of transactions made on maplerad also and prepare a competitive analysis then send to my mail vieester4920@gmail.com"):
    if event_type == "tool_call":
        print(f"  ⚙  {content}")
    elif event_type == "answer":
        print(f"\nIvy: {content}")

