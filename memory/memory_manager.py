"""
Memory system for RootCause AI
"""
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class ShortTermMemory:
    """In-session memory for current debugging session"""

    def __init__(self, max_size: int = 50):
        self.memory = deque(maxlen=max_size)
        self.context_stack = []

    def add(self, entry: Dict[str, Any]):
        """Add entry to memory"""
        entry["timestamp"] = datetime.now().isoformat()
        self.memory.append(entry)

    def get_all(self) -> List[Dict]:
        """Get all memory entries"""
        return list(self.memory)

    def search(self, query: str) -> List[Dict]:
        """Search memory for entries matching query"""
        results = []
        query_lower = query.lower()

        for entry in self.memory:
            for value in entry.values():
                if isinstance(value, str) and query_lower in value.lower():
                    results.append(entry)
                    break

        return results

    def push_context(self, context: Dict[str, Any]):
        """Push context onto stack"""
        self.context_stack.append(context)

    def pop_context(self) -> Optional[Dict[str, Any]]:
        """Pop context from stack"""
        if self.context_stack:
            return self.context_stack.pop()
        return None

    def get_current_context(self) -> Optional[Dict[str, Any]]:
        """Get current context"""
        if self.context_stack:
            return self.context_stack[-1]
        return None

    def clear(self):
        """Clear all memory"""
        self.memory.clear()
        self.context_stack.clear()


class LongTermMemory:
    """Persistent memory across sessions"""

    def __init__(self, storage_path: str = "./data/long_term_memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.bug_patterns = self._load_bug_patterns()
        self.solutions = self._load_solutions()

    def _load_bug_patterns(self) -> List[Dict]:
        """Load previously identified bug patterns"""
        try:
            patterns_file = self.storage_path / "bug_patterns.json"
            if patterns_file.exists():
                with open(patterns_file, "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading bug patterns: {e}")
            return []

    def _load_solutions(self) -> List[Dict]:
        """Load previously found solutions"""
        try:
            solutions_file = self.storage_path / "solutions.json"
            if solutions_file.exists():
                with open(solutions_file, "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading solutions: {e}")
            return []

    def add_bug_pattern(self, pattern: Dict[str, Any]):
        """Store a bug pattern for future reference"""
        try:
            pattern["discovered_at"] = datetime.now().isoformat()
            self.bug_patterns.append(pattern)
            self._save_bug_patterns()
        except Exception as e:
            logger.error(f"Error adding bug pattern: {e}")

    def add_solution(self, solution: Dict[str, Any]):
        """Store a solution for future reference"""
        try:
            solution["discovered_at"] = datetime.now().isoformat()
            self.solutions.append(solution)
            self._save_solutions()
        except Exception as e:
            logger.error(f"Error adding solution: {e}")

    def search_similar_bugs(self, bug_description: str, top_k: int = 5) -> List[Dict]:
        """Search for similar bugs in history"""
        # Simple string matching (could be enhanced with embeddings)
        similar = []
        query_terms = bug_description.lower().split()

        for pattern in self.bug_patterns:
            description = pattern.get("description", "").lower()
            matches = sum(1 for term in query_terms if term in description)

            if matches > 0:
                similar.append((pattern, matches))

        # Sort by match count and return top-k
        similar.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in similar[:top_k]]

    def search_similar_solutions(self, problem_description: str, top_k: int = 5) -> List[Dict]:
        """Search for similar solutions in history"""
        similar = []
        query_terms = problem_description.lower().split()

        for solution in self.solutions:
            description = solution.get("problem_description", "").lower()
            matches = sum(1 for term in query_terms if term in description)

            if matches > 0:
                similar.append((solution, matches))

        similar.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in similar[:top_k]]

    def get_statistics(self) -> Dict:
        """Get statistics on stored patterns and solutions"""
        return {
            "total_bug_patterns": len(self.bug_patterns),
            "total_solutions": len(self.solutions),
            "recent_patterns": self.bug_patterns[-5:] if self.bug_patterns else [],
            "recent_solutions": self.solutions[-5:] if self.solutions else [],
        }

    def _save_bug_patterns(self):
        """Save bug patterns to disk"""
        try:
            patterns_file = self.storage_path / "bug_patterns.json"
            with open(patterns_file, "w") as f:
                json.dump(self.bug_patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving bug patterns: {e}")

    def _save_solutions(self):
        """Save solutions to disk"""
        try:
            solutions_file = self.storage_path / "solutions.json"
            with open(solutions_file, "w") as f:
                json.dump(self.solutions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving solutions: {e}")


class MemoryManager:
    """Unified memory management"""

    def __init__(self, short_term_max_size: int = 50, long_term_path: str = "./data/long_term_memory"):
        self.short_term = ShortTermMemory(max_size=short_term_max_size)
        self.long_term = LongTermMemory(storage_path=long_term_path)

    def record_session_event(self, agent_name: str, action: str, details: Dict):
        """Record event during session"""
        self.short_term.add(
            {
                "agent": agent_name,
                "action": action,
                "details": details,
            }
        )

    def record_bug_finding(self, bug_pattern: Dict[str, Any]):
        """Record a bug finding for long-term memory"""
        self.long_term.add_bug_pattern(bug_pattern)

    def record_solution(self, solution: Dict[str, Any]):
        """Record a solution for long-term memory"""
        self.long_term.add_solution(solution)

    def get_session_summary(self) -> Dict:
        """Get summary of current session"""
        return {
            "session_events": len(self.short_term.memory),
            "events": self.short_term.get_all(),
        }

    def get_memory_stats(self) -> Dict:
        """Get statistics on all memory"""
        return {
            "short_term": {
                "entries": len(self.short_term.memory),
                "max_size": self.short_term.memory.maxlen,
            },
            "long_term": self.long_term.get_statistics(),
        }
