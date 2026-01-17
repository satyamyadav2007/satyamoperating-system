import logging
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage

# --- PILLAR 1: AGENT PERMISSIONS (The Sandbox) ---
class PermissionEngine:
    """
    Acts as a firewall. Agents cannot call tools directly.
    They must pass through this proxy.
    """
    def __init__(self):
        # Define RBAC (Role Based Access Control)
        self.policy = {
            "research_agent": ["search_web", "read_email"],
            "finance_agent": ["read_email", "execute_payment"],
            "junior_agent": ["search_web"] # Cannot spend money
        }

    def verify_action(self, agent_role: str, tool_name: str) -> bool:
        allowed_tools = self.policy.get(agent_role, [])
        if tool_name in allowed_tools:
            return True
        logging.warning(f"SECURITY ALERT: {agent_role} tried to use unauthorized tool: {tool_name}")
        return False

# --- PILLAR 2: AGENT MEMORY (The Hippocampus) ---
class MemoryManager:
    """
    Consolidates short-term context into long-term storage.
    """
    def __init__(self):
        # In a real app, use Pinecone or Weaviate here
        self.short_term = {} # Redis-style session cache
        self.long_term = []  # Vector DB stub

    def save_context(self, agent_id: str, content: str):
        # Feature: "Memory Consolidation"
        # If context is > 4000 chars, summarize and move to long-term
        if len(content) > 4000:
            summary = f"Summary of: {content[:50]}..." 
            self.long_term.append({"id": agent_id, "memory": summary})
            return "Context compressed and archived."
        
        self.short_term[agent_id] = content
        return "Saved to active RAM."