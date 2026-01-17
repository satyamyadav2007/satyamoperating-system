import os
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Import your local modules (ensure these files exist in your project)
from os_kernel import PermissionEngine, MemoryManager
from tools import AgentTools 

# Define the State of the OS
class AgentState(TypedDict):
    messages: list
    current_agent: str
    error_count: int

class AgentOrchestrator:
    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Correct: Aligned with the line above
        self.permissions = PermissionEngine()
        self.memory = MemoryManager()
        
        # 2. Setup LLM (OpenRouter configuration)
        self.llm = ChatOpenAI(
            model="meta-llama/llama-3.3-70b-instruct:free",
            openai_api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "AgentOS Platform"
            }
        )

        # 3. Map Tools for the Agent to use
        # This maps the string name the LLM returns to the actual Python function
        self.available_tools = {
            "read_email": AgentTools.read_emails,
            "execute_python": AgentTools.execute_python  # Ensure this exists in AgentTools
        }

        # --- PILLAR 2: GRAPH CONSTRUCTION ---
        self.workflow = StateGraph(AgentState)
        
        # Add Nodes
        self.workflow.add_node("supervisor", self.supervisor_node)
        self.workflow.add_node("worker", self.worker_node)
        self.workflow.add_node("retry_handler", self.recovery_node)
        
        # Define Edges (The Flow)
        self.workflow.set_entry_point("supervisor")
        self.workflow.add_edge("supervisor", "worker")
        
        # Conditional Logic: Check health after worker runs
        self.workflow.add_conditional_edges(
            "worker",
            self.check_health,
            {
                "ok": END,
                "error": "retry_handler"
            }
        )
        # If retry happens, go back to worker
        self.workflow.add_edge("retry_handler", "worker")
        
        # Compile
        self.app = self.workflow.compile()

    # --- PILLAR 3: NODE LOGIC ---

    def supervisor_node(self, state: AgentState):
        """Decides which agent performs the task and initializes error count."""
        print("--- [Supervisor] Assigning task to Research Agent ---")
        return {"current_agent": "research_agent", "error_count": 0}

    def worker_node(self, state: AgentState):
        """The core logic: THINK (LLM) -> CHECK (Security) -> ACT (Tools)"""
        agent_role = state['current_agent']
        
        # Get the user's task from the message history
        last_message = state['messages'][-1] if state['messages'] else HumanMessage(content="Check my emails")
        user_task = last_message.content if hasattr(last_message, 'content') else str(last_message)

        print(f"--- [Worker: {agent_role}] Processing: {user_task} ---")

        # 1. THINK: Bind tools and ask LLM what to do
        llm_with_tools = self.llm.bind_tools([
            {"type": "function", "function": {"name": "read_email", "description": "Read user emails"}},
            {"type": "function", "function": {"name": "execute_python", "description": "Run Python code to solve math or data tasks"}}
        ])
        
        try:
            # Send context to LLM
            response = llm_with_tools.invoke([
                SystemMessage(content=f"You are {agent_role}. You verify permissions before acting. Choose a tool if needed."),
                HumanMessage(content=user_task)
            ])
        except Exception as e:
            return {"messages": [f"ERROR: LLM invocation failed - {str(e)}"]}

        # 2. DECIDE & CHECK PERMISSIONS
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            print(f"--- [Worker] LLM wants to use tool: {tool_name} ---")

            # A. Security Check (The Guardrail)
            if self.permissions.verify_action(agent_role, tool_name):
                
                # B. Execute Tool (ACT)
                if tool_name in self.available_tools:
                    try:
                        # Special handling for tools that need arguments (like 'execute_python')
                        if tool_name == "execute_python":
                            code_to_run = tool_args.get("code", "")
                            tool_result = self.available_tools[tool_name](code_to_run)
                        else:
                            # Standard execution for tools like 'read_email'
                            tool_result = self.available_tools[tool_name]()
                        
                        # C. Memory Storage
                        self.memory.save_context(agent_role, str(tool_result))
                        
                        return {"messages": [f"SUCCESS: {tool_result}"]}
                    except Exception as e:
                        return {"messages": [f"ERROR: Tool execution failed - {str(e)}"]}
                else:
                    return {"messages": [f"ERROR: Tool {tool_name} not found in available_tools"]}
            else:
                return {"messages": ["SECURITY ERROR: Permission Denied for this agent."]}
        
        # If no tool was called, just return the LLM's text response
        return {"messages": [response.content]}

    # --- PILLAR 4: RECOVERY & HEALTH ---

    def check_health(self, state: AgentState):
        """Checks the last message for error keywords."""
        if not state["messages"]:
            return "ok"
            
        last_msg = state["messages"][-1]
        content = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
        
        if "ERROR" in content or "Exception" in content:
            return "error"
        return "ok"

    def recovery_node(self, state: AgentState):
        """Self-healing logic: increment error count and retry."""
        current_errors = state.get("error_count", 0)
        
        if current_errors >= 3:
            return {"messages": ["CRITICAL FAILURE: Max retries exceeded. Shutting down agent."]}
            
        print(f"⚠️ [System] Failure Detected. Retry {current_errors + 1}/3...")
        
        return {
            "error_count": current_errors + 1,
            "messages": ["System Note: Retrying operation..."]
        }