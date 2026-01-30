"""
Task Extractor Service for Atlas AI Beta Features
Parses conversations to extract tasks and create to-do lists
"""
import re
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

class TaskExtractor:
    """Service for extracting tasks from conversations and managing task lists."""

    def __init__(self):
        self.tasks_file = Path(__file__).parent.parent / "data" / "tasks.json"
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)

    def extract_tasks_from_message(self, message: str, message_id: str = None) -> List[Dict[str, Any]]:
        """
        Extract potential tasks from a single message.
        Returns a list of task dictionaries.
        """
        tasks = []

        # Patterns for task detection
        task_patterns = [
            # Explicit task markers
            r'(?i)(?:todo|task|action item|next step|reminder)[\s:]+(.+)',
            r'(?i)(?:need to|should|must|have to)[\s]+(.+)',
            r'(?i)don\'t forget to[\s]+(.+)',
            r'(?i)remember to[\s]+(.+)',

            # Bullet points and numbered lists
            r'(?:^|\n)[\s]*[-*•]\s*(.+?)(?:\n|$)',
            r'(?:^|\n)[\s]*\d+\.\s*(.+?)(?:\n|$)',

            # Questions that imply tasks
            r'(?i)(?:can you|could you|would you)[\s]+(.+)\?',

            # Time-based tasks
            r'(?i)(?:later|tomorrow|next week|soon)[\s]*[:,-]?\s*(.+)',
        ]

        for pattern in task_patterns:
            matches = re.finditer(pattern, message, re.MULTILINE)
            for match in matches:
                task_text = match.group(1).strip()
                if len(task_text) > 5 and len(task_text) < 200:  # Reasonable length
                    tasks.append({
                        'id': f"{message_id}_{len(tasks)}" if message_id else f"temp_{len(tasks)}",
                        'text': task_text,
                        'source_message_id': message_id,
                        'confidence': self._calculate_confidence(task_text, pattern),
                        'status': 'pending',
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    })

        return tasks

    def extract_tasks_from_conversation(self, messages: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extract tasks from an entire conversation.
        Returns deduplicated list of tasks.
        """
        all_tasks = []
        seen_texts = set()

        for message in messages:
            if message.get('role') == 'assistant':
                message_tasks = self.extract_tasks_from_message(
                    message.get('content', ''),
                    message.get('id')
                )
                all_tasks.extend(message_tasks)

        # Deduplicate and prioritize
        unique_tasks = []
        for task in all_tasks:
            # Simple deduplication based on text similarity
            task_key = task['text'].lower().strip()
            if task_key not in seen_texts:
                seen_texts.add(task_key)
                unique_tasks.append(task)

        # Sort by confidence
        unique_tasks.sort(key=lambda x: x['confidence'], reverse=True)

        return unique_tasks[:20]  # Limit to top 20 tasks

    def _calculate_confidence(self, task_text: str, pattern: str) -> float:
        """Calculate confidence score for extracted task."""
        confidence = 0.5  # Base confidence

        # Boost confidence for explicit task markers
        if re.search(r'(?i)todo|task|action item', pattern):
            confidence += 0.3

        # Boost for actionable language
        if re.search(r'(?i)need to|should|must|have to', task_text):
            confidence += 0.2

        # Reduce confidence for questions
        if task_text.endswith('?'):
            confidence -= 0.1

        # Reduce confidence for very short tasks
        if len(task_text.split()) < 3:
            confidence -= 0.2

        return max(0.1, min(1.0, confidence))

    def save_tasks(self, tasks: List[Dict[str, Any]], chat_id: str = None):
        """Save tasks to persistent storage."""
        try:
            existing_data = self._load_tasks()

            if chat_id:
                existing_data['chat_tasks'][chat_id] = tasks
            else:
                existing_data['global_tasks'].extend(tasks)

            # Remove duplicates across global tasks
            seen_texts = set()
            deduplicated = []
            for task in existing_data['global_tasks']:
                text_key = task['text'].lower().strip()
                if text_key not in seen_texts:
                    seen_texts.add(text_key)
                    deduplicated.append(task)

            existing_data['global_tasks'] = deduplicated[-100:]  # Keep last 100

            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"[TaskExtractor] Error saving tasks: {e}")

    def load_tasks_for_chat(self, chat_id: str) -> List[Dict[str, Any]]:
        """Load tasks for a specific chat."""
        try:
            data = self._load_tasks()
            return data.get('chat_tasks', {}).get(chat_id, [])
        except Exception as e:
            print(f"[TaskExtractor] Error loading tasks for chat {chat_id}: {e}")
            return []

    def load_global_tasks(self) -> List[Dict[str, Any]]:
        """Load global tasks."""
        try:
            data = self._load_tasks()
            return data.get('global_tasks', [])
        except Exception as e:
            print(f"[TaskExtractor] Error loading global tasks: {e}")
            return []

    def update_task_status(self, task_id: str, status: str, chat_id: str = None):
        """Update the status of a task."""
        try:
            data = self._load_tasks()

            # Search in chat-specific tasks
            if chat_id and chat_id in data.get('chat_tasks', {}):
                for task in data['chat_tasks'][chat_id]:
                    if task['id'] == task_id:
                        task['status'] = status
                        task['updated_at'] = datetime.now().isoformat()
                        break

            # Search in global tasks
            for task in data.get('global_tasks', []):
                if task['id'] == task_id:
                    task['status'] = status
                    task['updated_at'] = datetime.now().isoformat()
                    break

            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"[TaskExtractor] Error updating task status: {e}")

    def _load_tasks(self) -> Dict[str, Any]:
        """Load tasks data from file."""
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[TaskExtractor] Error loading tasks file: {e}")

        return {
            'chat_tasks': {},
            'global_tasks': []
        }

# Global instance
_task_extractor = None

def get_task_extractor():
    """Get the global task extractor instance."""
    global _task_extractor
    if _task_extractor is None:
        _task_extractor = TaskExtractor()
    return _task_extractor