from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import time

@dataclass
class Message:
    """聊天消息类"""
    
    def __init__(
        self,
        role: str,
        text: str = None,
        priority: float = 1.0,
        files: List[str] = None,
        timestamp: float = None,
        tool_calls: List[Dict] = None,
        tool_call_id: str = None,
        name: str = None,
        content: List[Dict] = None
    ):
        self.role = role
        self.text = text
        self.priority = priority
        self.files = files or []
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.tool_calls = tool_calls or []
        self.tool_call_id = tool_call_id
        self.name = name
        self.content = content