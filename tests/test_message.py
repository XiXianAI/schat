import pytest
from schat.core.message import Message
from datetime import datetime

def test_message_creation():
    msg = Message(role="user", text="Hello")
    assert msg.role == "user"
    assert msg.text == "Hello"
    assert msg.priority == 1.0
    assert isinstance(msg.timestamp, float)
    assert msg.files == []
    assert msg.tool_calls == []

def test_message_with_files():
    msg = Message(role="user", text="Check this", files=["doc1.pdf"])
    assert len(msg.files) == 1
    assert msg.files[0] == "doc1.pdf"

def test_message_with_tool_calls():
    tool_call = {"name": "weather", "args": {"location": "Beijing"}}
    msg = Message(role="assistant", text="Weather info", tool_calls=[tool_call])
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0] == tool_call

def test_message_timestamp():
    before = datetime.now().timestamp()
    msg = Message(role="user", text="Hello")
    after = datetime.now().timestamp()
    assert before <= msg.timestamp <= after

def test_message_custom_timestamp():
    custom_time = 1234567890.0
    msg = Message(role="user", text="Hello", timestamp=custom_time)
    assert msg.timestamp == custom_time

def test_message_priority():
    msg = Message(role="user", text="Hello", priority=2.0)
    assert msg.priority == 2.0

def test_message_with_name():
    msg = Message(role="assistant", text="Hello", name="helper")
    assert msg.name == "helper"

def test_message_with_tool_call_id():
    msg = Message(
        role="assistant", 
        text="Result",
        tool_call_id="weather_123"
    )
    assert msg.tool_call_id == "weather_123"

def test_message_with_multiple_files():
    files = ["doc1.pdf", "img1.jpg", "doc2.txt"]
    msg = Message(role="user", text="Check these", files=files)
    assert len(msg.files) == 3
    assert msg.files == files

def test_message_with_complex_tool_calls():
    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "weather",
                "arguments": {"location": "Beijing"}
            }
        },
        {
            "id": "call_2",
            "type": "function",
            "function": {
                "name": "time",
                "arguments": {"timezone": "UTC"}
            }
        }
    ]
    msg = Message(role="assistant", text="Results", tool_calls=tool_calls)
    assert len(msg.tool_calls) == 2
    assert msg.tool_calls[0]["id"] == "call_1"
    assert msg.tool_calls[1]["function"]["name"] == "time"