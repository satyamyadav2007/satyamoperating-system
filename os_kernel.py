import logging
import sqlite3
import json
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage

# Logging setup takki terminal mein alerts dikhein
logging.basicConfig(level=logging.INFO)

# --- PILLAR 2: AGENT MEMORY (The Hippocampus) ---
class MemoryManager:
    """
    Consolidates short-term context into long-term SQLite storage.
    """
    def __init__(self, db_path="agent_os.db"):
        self.db_path = db_path
        self.short_term = {} # Session cache
        self._bootstrap_db()

    def _bootstrap_db(self):
        """Database aur Table create karta hai agar nahi bani toh."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                context_key TEXT,
                context_value TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logging.info("✅ SQLite Database connected and initialized.")

    def save_context(self, agent_id: str, key: str, value: Any):
        """Permanent storage mein memory save karta hai."""
        # Feature: Memory Consolidation
        content_str = str(value)
        if len(content_str) > 4000:
            content_str = f"Summary: {content_str[:100]}... [Archived]"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO agent_memory (agent_id, context_key, context_value) VALUES (?, ?, ?)",
            (agent_id, key, content_str)
        )
        conn.commit()
        conn.close()
        self.short_term[agent_id] = content_str
        return "Memory stored in persistent DB."

    def get_memory(self, agent_id: str):
        """Agent ki saari purani yaadein nikalta hai."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT context_key, context_value FROM agent_memory WHERE agent_id = ?", (agent_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows

# --- PILLAR 1: AGENT PERMISSIONS (The Firewall) ---
class PermissionEngine:
    """
    Agents cannot call tools directly. They must pass through this proxy.
    """
    def __init__(self):
        # Define RBAC (Role Based Access Control)
        self.policy = {
            "research_agent": ["search_web", "read_email"],
            "finance_agent": ["read_email", "execute_payment"],
            "junior_agent": ["search_web"] 
        }

    def verify_action(self, agent_role: str, tool_name: str) -> bool:
        allowed_tools = self.policy.get(agent_role, [])
        if tool_name in allowed_tools:
            return True
        logging.warning(f"🚨 SECURITY ALERT: {agent_role} unauthorized tool: {tool_name}")
        return False