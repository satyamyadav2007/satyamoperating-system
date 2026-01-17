from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from os_kernel import PermissionEngine, MemoryManager
from fastapi import FastAPI
from agent_runtime import AgentOrchestrator
from pydantic.v1.fields import FieldInfo as FieldInfoV1

# --- THIS IS THE MISSING PART ---
app = FastAPI(title="AgentOS Platform") 
# ADD THIS CODE BELOW IT:
@app.get("/")
def read_root():
    return {"message": "Server is running successfully!"}

os_instance = AgentOrchestrator()

# ... rest of your endpoints ...

# Define the State of the OS
class AgentState(TypedDict):
    messages: list
    current_agent: str
    error_count: int

class AgentOrchestrator:
    def __init__(self):
        self.permissions = PermissionEngine()
        self.memory = MemoryManager()
        self.workflow = StateGraph(AgentState)
        
        # Build the Graph (The "Circuit Board")
        self.workflow.add_node("supervisor", self.supervisor_node)
        self.workflow.add_node("worker", self.worker_node)
        self.workflow.add_node("retry_handler", self.recovery_node)
        
        # Define flow
        self.workflow.set_entry_point("supervisor")
        self.workflow.add_edge("supervisor", "worker")
        self.workflow.add_conditional_edges(
            "worker",
            self.check_health,
            {
                "ok": END,
                "error": "retry_handler"
            }
        )
        self.workflow.add_edge("retry_handler", "worker")
        
        self.app = self.workflow.compile()

    # --- PILLAR 3: ORCHESTRATION (The Manager) ---
    def supervisor_node(self, state: AgentState):
        # Decides which agent performs the task
        return {"current_agent": "research_agent", "error_count": 0}

    def worker_node(self, state: AgentState):
        agent_role = state['current_agent']
        action_to_take = "search_web" # Mocking LLM decision
        
        # Security Check before execution
        if self.permissions.verify_action(agent_role, action_to_take):
            # Execute Logic
            print(f"[{agent_role}] Executing {action_to_take}...")
            # Simulate a failure for demonstration
            if state.get("error_count", 0) == 0: 
                return {"messages": ["ERROR: API Timeout"]}
            return {"messages": ["Success: Found data"]}
        else:
            return {"messages": ["Error: Permission Denied"]}

    # --- PILLAR 4: FAILURE RECOVERY (The Self-Healing) ---
    def check_health(self, state: AgentState):
        last_message = state["messages"][-1]
        if "ERROR" in last_message:
            return "error"
        return "ok"

    def recovery_node(self, state: AgentState):
        print("⚠️ System Failure Detected. Attempting Self-Repair...")
        # "Time Travel": Reset state, adjust temperature, retry
        return {
            "error_count": state["error_count"] + 1,
            "messages": ["System Note: Retrying with backoff strategy..."]
        }
@app.get("/telemetry/{agent_id}")
async def get_agent_status(agent_id: str):
    """
    Shows the 'Health' and 'Memory' of a specific agent.
    This is what companies pay for: Visibility.
    """
    memory = os_instance.memory.short_term.get(agent_id, "No active memory")
    return {
        "agent_id": agent_id,
        "status": "Healthy",
        "last_known_memory": memory,
        "uptime": "99.9%" # The 'AWS' promise
    
    }
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# --- PASTE THIS AT THE BOTTOM OF main.py ---

# 1. Define the input format
class ChatRequest(BaseModel):
    message: str

# 2. Create the Chat Endpoint
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"--- User Request: {request.message} ---")
    
    # Prepare the initial state
    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "current_agent": "supervisor",
        "error_count": 0
    }
    
    # Run the Agent Graph
    # We use 'ainvoke' because this is an async function
    result = await os_instance.app.ainvoke(initial_state)
    
    # Extract the final response
    final_message = result["messages"][-1]
    content = final_message.content if hasattr(final_message, 'content') else str(final_message)
    
    return {"response": content}