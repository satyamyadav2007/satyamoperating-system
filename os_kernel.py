import logging
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage
import sqlite3
import json

class MemoryManager:
    def __init__(self, db_path="agent_os.db"):
        self.db_path = db_path
        self._bootstrap_db()

    def _bootstrap_db(self):
        """Creates the database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_memory (
                agent_id TEXT,
                context_key TEXT,
                context_value TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def save_context(self, agent_id: str, key: str, value: Any):
        """Saves memory to permanent storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO agent_memory (agent_id, context_key, context_value) VALUES (?, ?, ?)",
            (agent_id, key, str(value))
        )
        conn.commit()
        conn.close()
        return "Memory stored in persistent DB."

    def get_memory(self, agent_id: str):
        """Retrieves all past memories for an agent."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT context_key, context_value FROM agent_memory WHERE agent_id = ?", (agent_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows
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