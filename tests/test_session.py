from typing import Generator, List
import pytest
import tempfile
import os
from schat.core.message import Message
from schat.core.session import ChatSession
from schat.models.base import Model
import json
from tests.conftest import MockModel

def test_chat_session_initialization(chat_session):
    assert isinstance(chat_session.default_model, Model)
    assert chat_session.history == []
    assert chat_session.system_prompt is None
    assert chat_session.stream is False

def test_set_system_prompt(chat_session):
    chat_session.set_system_prompt("You are a helpful assistant")
    assert chat_session.system_prompt == "You are a helpful assistant"

def test_add_user_message(chat_session):
    msg = chat_session.add_user_message("Hello", files=["doc.pdf"])
    assert msg.role == "user"
    assert msg.text == "Hello"
    assert msg.files == ["doc.pdf"]
    assert len(chat_session.history) == 1

def test_add_assistant_message(chat_session):
    msg = chat_session.add_assistant_message("Hi", tool_calls=[{"name": "test"}])
    assert msg.role == "assistant"
    assert msg.text == "Hi"
    assert msg.tool_calls == [{"name": "test"}]
    assert len(chat_session.history) == 1

def test_send_message(chat_session, mock_model):
    mock_model.set_responses(["Hello! How can I help?"])
    response = chat_session.send("Hello!")
    assert isinstance(response, Message)
    assert response.role == "assistant"
    assert response.text == "Hello! How can I help?"
    assert len(chat_session.history) == 2

def test_send_message_with_stream(chat_session, mock_model):
    mock_model.set_responses(["Hello!"])
    response = chat_session.send("Hi", stream=True)
    assert isinstance(response, Generator)
    text = "".join(list(response))
    assert text == "Hello!"
    assert len(chat_session.history) == 1  # 流式响应不添加到历史

def test_save_load_session(chat_session):
    chat_session.add_user_message("Hello")
    chat_session.add_assistant_message("Hi")
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        chat_session.save(tmp.name)
        
        new_session = ChatSession()
        new_session.load(tmp.name)
        
        assert len(new_session.history) == len(chat_session.history)
        assert isinstance(new_session.default_model, type(chat_session.default_model))
        assert new_session.default_model.get_model_config() == chat_session.default_model.get_model_config()
        
    os.unlink(tmp.name)

def test_get_current_round(chat_session):
    assert chat_session.get_current_round() == 0
    chat_session.add_user_message("Hello")
    chat_session.add_assistant_message("Hi")
    assert chat_session.get_current_round() == 1

def test_truncate_history(chat_session):
    # Add 3 rounds of messages
    for i in range(3):
        chat_session.add_user_message(f"Hello {i}")
        chat_session.add_assistant_message(f"Hi {i}")
    
    assert len(chat_session.history) == 6
    chat_session.truncate_history(2)
    assert len(chat_session.history) == 4

def test_set_priority(chat_session):
    chat_session.add_user_message("Hello")
    chat_session.add_assistant_message("Hi")
    chat_session.add_user_message("How are you?")
    chat_session.add_assistant_message("Good!")
    
    chat_session.set_priority(0, 2.0)
    assert chat_session.history[0].priority == 2.0
    assert chat_session.history[1].priority == 2.0

def test_send_with_files(chat_session, mock_model):
    mock_model.set_responses(["Analyzed the document"])
    response = chat_session.send(
        "Please analyze this",
        files=["doc1.pdf", "doc2.pdf"]
    )
    assert len(chat_session.history[0].files) == 2
    assert response.text == "Analyzed the document"

def test_send_with_tools(chat_session, mock_model):
    tools = [{"name": "weather", "args": {"location": "Beijing"}}]
    mock_model.set_responses(["Weather is sunny"])
    response = chat_session.send("Get weather", tools=tools)
    assert chat_session.history[0].tool_calls == tools

def test_send_with_priority(chat_session, mock_model):
    mock_model.set_responses(["Important response"])
    response = chat_session.send("Important message", priority=2.0)
    assert chat_session.history[0].priority == 2.0

def test_prepare_messages(chat_session):
    chat_session.set_system_prompt("You are helpful")
    chat_session.add_user_message("Hello")
    chat_session.add_assistant_message("Hi")
    
    messages = chat_session._prepare_messages()
    assert len(messages) == 3
    assert messages[0].role == "system"
    assert messages[1].role == "user"
    assert messages[2].role == "assistant"

def test_session_with_stream_default(mock_model):
    session = ChatSession(default_model=mock_model, stream=True)
    mock_model.set_responses(["Streaming response"])
    response = session.send("Hello")
    assert isinstance(response, Generator)

def test_stream_override(chat_session, mock_model):
    # Session默认不使用stream，但可以在send时覆盖
    mock_model.set_responses(["Override to stream"])
    response = chat_session.send("Hello", stream=True)
    assert isinstance(response, Generator)
    
    # 同样可以覆盖为False
    session = ChatSession(default_model=mock_model, stream=True)
    mock_model.set_responses(["Override to normal"])
    response = session.send("Hello", stream=False)
    assert isinstance(response, Message)

def test_invalid_model():
    session = ChatSession()
    with pytest.raises(ValueError, match="No model specified"):
        session.send("Hello")

def test_save_load_with_stream(chat_session):
    chat_session.stream = True
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        chat_session.save(tmp.name)
        new_session = ChatSession()
        new_session.load(tmp.name)
        assert new_session.stream == True
    os.unlink(tmp.name)

def test_invalid_priority_round(chat_session):
    chat_session.add_user_message("Hello")
    chat_session.add_assistant_message("Hi")
    
    # 测试负数轮次
    chat_session.set_priority(-1, 2.0)
    assert chat_session.history[0].priority == 1.0
    
    # 测试超出范围的轮次
    chat_session.set_priority(1, 2.0)
    assert chat_session.history[0].priority == 1.0

def test_empty_truncate(chat_session):
    chat_session.add_user_message("Hello")
    chat_session.truncate_history(1)
    assert len(chat_session.history) == 1  # 不应该截断

def test_save_load_error_handling():
    session = ChatSession()
    
    # 测试保存到无效路径
    with pytest.raises(IOError):
        session.save("/invalid/path/session.json")
    
    # 测试加载不存在的文件
    with pytest.raises(FileNotFoundError):
        session.load("nonexistent.json")
    
    # 测试加载损坏的文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write("invalid json")
    
    with pytest.raises(json.JSONDecodeError):
        session.load(tmp.name)
    
    os.unlink(tmp.name)

def test_prepare_messages_empty_session(chat_session):
    messages = chat_session._prepare_messages()
    assert len(messages) == 0
    
    chat_session.set_system_prompt("System")
    messages = chat_session._prepare_messages()
    assert len(messages) == 1
    assert messages[0].role == "system"

def test_get_model(chat_session, mock_model):
    # 测试传入Model实例
    model = chat_session._get_model(mock_model)
    assert model is mock_model
    
    # 测试使用默认模型
    model = chat_session._get_model(None)
    assert model is chat_session.default_model
    
    # 测试传入模型名称
    model = chat_session._get_model("mock")
    assert isinstance(model, MockModel)
    
    # 测试错误情况
    chat_session.default_model = None
    with pytest.raises(ValueError):
        chat_session._get_model(None)

def test_get_history(chat_session):
    # 测试空历史
    history = chat_session._get_history()
    assert len(history) == 0
    
    # 添加系统提示
    chat_session.set_system_prompt("System message")
    history = chat_session._get_history()
    assert len(history) == 1
    assert history[0].role == "system"
    
    # 添加用户消息
    chat_session.add_message(Message(role="user", text="User message"))
    history = chat_session._get_history()
    assert len(history) == 2
    assert history[1].role == "user"

def test_tool_message_handling(chat_session):
    # 测试字符串结果
    tool_msg = chat_session.add_tool_message("result", "call_123")
    assert tool_msg.role == "tool"
    assert tool_msg.text == "result"
    assert tool_msg.tool_call_id == "call_123"
    
    # 测试字典结果
    result = {"key": "value"}
    tool_msg = chat_session.add_tool_message(result, "call_456")
    assert tool_msg.role == "tool"
    assert tool_msg.text == '{"key": "value"}'
    assert tool_msg.tool_call_id == "call_456"