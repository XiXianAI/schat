import pytest
from schat.models.base import Model
from schat.core.message import Message
from typing import Generator
from tests.conftest import MockModel  # 使用绝对导入

def test_model_api_key():
    model = MockModel()
    model.set_api_key("test-key")
    assert model.api_key == "test-key"

def test_model_stream_response(mock_model):
    mock_model.set_responses(["Hello", "World"])
    messages = [Message(role="user", text="Hi")]
    
    response = mock_model.send(messages, stream=True)
    assert isinstance(response, Generator)
    
    text = "".join(list(response))
    assert text == "Hello"

def test_model_normal_response(mock_model):
    mock_model.set_responses(["Normal response"])
    messages = [Message(role="user", text="Hi")]
    
    response = mock_model.send(messages)
    assert isinstance(response, Message)
    assert response.text == "Normal response"

def test_model_with_files(mock_model):
    mock_model.set_responses(["Processed files"])
    messages = [
        Message(
            role="user",
            text="Process these",
            files=["file1.pdf", "file2.jpg"]
        )
    ]
    
    response = mock_model.send(messages)
    assert response.text == "Processed files"

def test_model_with_tools(mock_model):
    mock_model.set_responses(["Used tools"])
    messages = [
        Message(
            role="user",
            text="Use tools",
            tool_calls=[{"name": "test_tool"}]
        )
    ]
    
    response = mock_model.send(messages)
    assert response.text == "Used tools"

def test_model_config_management(mock_model):
    # 测试默认配置
    default_config = mock_model.get_model_config()
    assert default_config["temperature"] == 0.7
    assert default_config["stream"] == False
    
    # 测试更新配置
    new_config = {"temperature": 0.9}
    mock_model.set_model_config(new_config)
    
    updated_config = mock_model.get_model_config()
    assert updated_config["temperature"] == 0.9
    assert updated_config["stream"] == False  # 未修改的配置保持不变