from typing import List, Dict
from dataclasses import dataclass

MAX_CACHED_MESSAGES = 4

@dataclass
class CacheConfig:
    type: str = "ephemeral"

def add_cache_to_messages(messages: List[Dict]) -> List[Dict]:
    """Add cache control to messages following specific rules.
    
    Args:
        messages: List of messages in Anthropic format
        
    Returns:
        List of messages with cache control added
    """
    # Track how many messages have cache control
    cache_count = 0
    messages_with_cache = []
    
    # Process system message first if exists
    if messages and messages[0]["role"] == "system":
        system_msg = messages[0].copy()
        for content in system_msg["content"]:
            content["cache_control"] = {"type": "ephemeral"}
        messages_with_cache.append(system_msg)
        cache_count += 1
        messages = messages[1:]
    
    # First pass: add cache to messages with files/images
    for msg in messages:
        msg_copy = msg.copy()
        has_non_text = False
        
        for content in msg_copy["content"]:
            if content["type"] != "text":
                content["cache_control"] = {"type": "ephemeral"}
                has_non_text = True
        
        if has_non_text and cache_count < MAX_CACHED_MESSAGES:
            cache_count += 1
            
        messages_with_cache.append(msg_copy)
    
    # Second pass: add cache to remaining messages from the end
    if cache_count < MAX_CACHED_MESSAGES:
        remaining = MAX_CACHED_MESSAGES - cache_count
        for msg in messages_with_cache[-remaining:]:
            for content in msg["content"]:
                if "cache_control" not in content:
                    content["cache_control"] = {"type": "ephemeral"}
    
    return messages_with_cache 