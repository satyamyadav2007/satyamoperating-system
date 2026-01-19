import os
import logging
from typing import TypedDict, List
from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# Apni purani os_kernel file se MemoryManager import karein
from os_kernel import MemoryManager

load_dotenv()

app = FastAPI()
memory = MemoryManager() # SQLite connect ho jayega

class AgentState(TypedDict):
    messages: List[str]
    user_id: str

class JobRequest(BaseModel):
    user_id: str
    task: str

class AgentOrchestrator:
    def __init__(self):
        # 1. LLM Setup (The Brain)
        self.llm = ChatOpenAI(
    # Model badal kar ye wala dalein (Jo free hai)
    model="google/gemini-2.0-flash-exp:free", 
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Agent OS Interface"
    }
)
        
        self.workflow = StateGraph(AgentState)
        self.workflow.add_node("agent", self.call_llm)
        self.workflow.set_entry_point("agent")
        self.workflow.add_edge("agent", END)
        self.app = self.workflow.compile()

    async def call_llm(self, state: AgentState):
        user_msg = state["messages"][-1]
        
        # 2. Memory se purani baatein nikalna (Optional upgrade)
        # past_memory = memory.get_memory(state["user_id"])
        
        # 3. AI se baat karna
        response = await self.llm.ainvoke(user_msg)
        ai_reply = response.content
        
        # 4. SQLite mein save karna (The Memory)
        memory.save_context(state["user_id"], "chat_history", ai_reply)
        
        return {"messages": [ai_reply]}

os_instance = AgentOrchestrator()

@app.post("/spawn_agent")
async def run_agent(job: JobRequest):
    initial_state = {"messages": [job.task], "user_id": job.user_id}
    result = await os_instance.app.ainvoke(initial_state)
    return {"status": "success", "response": result["messages"][-1]}
print(f"DEBUG: Key Loaded -> {os.getenv('OPENROUTER_API_KEY')[:10]}...")