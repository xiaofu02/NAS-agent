# runtime/memory_store.py

from config.settings import SYSTEM_PROMPT, MAX_TURNS


class MemoryStore:
    def __init__(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def reset(self):
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def add_user(self, content: str):
        self.messages.append({"role": "user", "content": content})
        self.trim()

    def add_assistant(self, content: str):
        self.messages.append({"role": "assistant", "content": content})

    def trim(self):
        system_msg = self.messages[0]
        history = self.messages[1:]
        max_msgs = MAX_TURNS * 2
        if len(history) > max_msgs:
            history = history[-max_msgs:]
        self.messages = [system_msg] + history

    def history_count(self) -> int:
        return len(self.messages) - 1

    def get_messages(self):
        return self.messages