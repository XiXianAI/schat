import pytest
import os
import base64
from typing import Generator
from schat.models.openai import OpenAIModel
from schat.core.message import Message
from schat.core.session import ChatSession
import json

class MockResponse:
    def __init__(self, content, tool_calls=None):
        message_attrs = {
            'content': content,
            'tool_calls': tool_calls
        }
        self.choices = [type('Choice', (), {
            'message': type('Message', (), message_attrs),
            'delta': type('Delta', (), {'content': content})
        })]
        self._content = content
        self._index = 0
        
    def __iter__(self):
        return self
        
    def __next__(self):
        if self._index >= len(self._content):
            raise StopIteration
        self._index += 1
        return type('Chunk', (), {
            'choices': [type('Choice', (), {
                'delta': type('Delta', (), {'content': self._content[self._index-1]})
            })]
        })

class MockOpenAI:
    def __init__(self, responses=None):
        self.chat = type('Chat', (), {
            'completions': type('Completions', (), {
                'create': lambda **kwargs: self._create(**kwargs)
            })
        })
        self.responses = responses or ["Mock response"]
        self.requests = []
        
    def _create(self, **kwargs):
        self.requests.append(kwargs)
        # 如果有tools参数，返回带工具调用的响应
        if "tools" in kwargs:
            tool_calls = [type('ToolCall', (), {
                'id': 'call_123',
                'type': 'function',
                'function': type('Function', (), {
                    'name': 'get_weather',
                    'arguments': '{"location": "Beijing"}'
                })
            })]
            return MockResponse("Calling weather function", tool_calls)
        return MockResponse(self.responses[0])

@pytest.fixture
def model():
    model = OpenAIModel()
    model.set_api_key("test-key")
    model.set_model_config({"model": "gpt-4o-mini"})
    return model

@pytest.fixture
def mock_openai(monkeypatch):
    mock = MockOpenAI()
    monkeypatch.setattr("openai.OpenAI", lambda **kwargs: mock)
    return mock

def test_basic_chat(model, mock_openai):
    messages = [Message(role="user", text="Hello")]
    response = model.send(messages)
    
    assert isinstance(response, Message)
    assert response.role == "assistant"
    assert response.text == "Mock response"

def test_streaming(model, mock_openai):
    messages = [Message(role="user", text="Hello")]
    response = model.send(messages, stream=True)
    
    assert isinstance(response, Generator)
    content = "".join(list(response))
    assert content == "Mock response"

def test_file_support(model, tmp_path):
    # 创建测试图片文件
    image_path = tmp_path / "test.jpg"
    with open(image_path, "wb") as f:
        f.write(b"fake image data")
    
    # 测试本地文件
    result = model.process_file(str(image_path))
    assert result["url"].startswith("data:image/jpeg;base64,")
    
    # 测试URL
    url = "https://example.com/image.jpg"
    result = model.process_file(url)
    assert result["url"] == url

def test_tools(model, mock_openai):
    weather_tool = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "parameters": {"location": "string"}
        }
    }
    
    response = model.send(
        [Message(role="user", text="What's the weather in Beijing?")],
        tools=[weather_tool]
    )
    
    assert len(response.tool_calls) > 0
    assert response.tool_calls[0]["function"]["name"] == "get_weather"

def test_api_key_management(monkeypatch, mock_openai):
    # 设置环境变量
    monkeypatch.setenv('OPENAI_KEY', 'env-key1,env-key2')
    
    model = OpenAIModel()
    model._key_manager.load_keys_from_env('openai')
    model.set_model_config({"model": "gpt-4o-mini"})
    
    # 测试自动获取key
    response = model.send([Message(role="user", text="Hello")])
    assert isinstance(response, Message)
    
    # 测试显式设置key
    model.set_api_key("explicit-key")
    response = model.send([Message(role="user", text="Hello")])
    assert isinstance(response, Message)

def test_base_url_configuration(model, mock_openai):
    model.set_base_url("https://custom.openai.api")
    model.send([Message(role="user", text="Hello")])
    assert model.base_url == "https://custom.openai.api" 

def test_tool_call_flow(model, mock_openai):
    # 1. 定义工具
    weather_tool = {
        "type": "function",
        "function": {
            "name": "get_weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "unit": {"type": "string", "enum": ["c", "f"]},
                },
                "required": ["location", "unit"],
                "additionalProperties": False,
            },
        },
    }
    
    # 2. 发送初始请求
    response = model.send(
        [Message(role="user", text="What's the weather in Paris?")],
        tools=[weather_tool],
        model="gpt-4o"  # 显式指定模型
    )
    
    # 验证工具调用请求
    assert len(response.tool_calls) > 0
    tool_call = response.tool_calls[0]
    assert tool_call["type"] == "function"
    assert tool_call["function"]["name"] == "get_weather"
    
    # 验证mock是否收到了正确的参数
    last_request = mock_openai.requests[-1]
    assert "tools" in last_request
    assert last_request["tools"] == [weather_tool]
    assert last_request["model"] == "gpt-4o"