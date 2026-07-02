from state import StudioState
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

class AgentMemory:
    @staticmethod
    def get_relevant_history(state: StudioState, agent_name: str, limit: int = 5) -> List[Dict]:
        history = state.get("conversation_history", [])
        relevant = [h for h in history if h.get("agent") == agent_name]
        return relevant[-limit:] if relevant else []
    
    @staticmethod
    def get_decision_memory(state: StudioState, context_key: str) -> Optional[Dict]:
        decisions = state.get("decision_memory", [])
        for decision in reversed(decisions):
            if decision.get("context") == context_key:
                return decision
        return None
    
    @staticmethod
    def add_conversation(state: StudioState, agent: str, role: str, content: str, metadata: Dict = None): # type: ignore
        history = state.get("conversation_history", [])
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        history.append(entry)
        state["conversation_history"] = history

    @staticmethod
    def add_decision(state: StudioState, context: str, decision: str, reasoning: str, outcome: str = ''):
        decisions = state.get("decision_memory", [])
        entry = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "decision": decision,
            "reasoning": reasoning,
            "outcome": outcome
        }
        decisions.append(entry)
        state["decision_memory"] = decisions

    @staticmethod
    def get_execution_trace(state: StudioState, agent_name: str = '') -> List[Dict]:
        trace = state.get("agent_trace", [])
        if agent_name:
            return [t for t in trace if t.get("agent") == agent_name]
        return trace
    
    @staticmethod
    def add_trace(state: StudioState, agent: str, action: str, data: Dict):
        trace = state.get("agent_trace", [])
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "data": data
        }
        trace.append(entry)
        state["agent_trace"] = trace