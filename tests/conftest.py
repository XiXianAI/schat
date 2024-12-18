import pytest
from schat import ChatSession, Message
from schat.models.base import Model
from schat.models.factory import ModelFactory
from typing import List, Generator, Union, Dict, Any

class MockModel(Model):
    """用于测试的模拟Model"""
    def __init__(self, provider: str = "mock", **kwargs):
        super().__init__(provider, **kwargs)
        self.client = None
        self.default_kwargs = {
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": False,
            "model": "mock-model"
        }
        self.responses = []
        
    def _ensure_client(self):
        """确保客户端已初始化"""
        if not self.client:
            self.client = "mock_client"
            
    def _prepare_request_kwargs(self, **kwargs) -> Dict:
        """准备请求参数"""
        request_kwargs = self.default_kwargs.copy()
        request_kwargs.update(kwargs)
        return request_kwargs
        
    def _send_llm(self, **kwargs) -> Any:
        """发送请求到模型"""
        if not self.responses:
            return "Mock response"
        return self.responses.pop(0)
        
    def _handle_stream(self, response) -> Generator[str, None, None]:
        """处理流式响应"""
        for char in response:
            yield char
            
    def _handle_response(self, response) -> Message:
        """处理普通响应"""
        return Message(role="assistant", text=response)
        
    def set_responses(self, responses: List[str]):
        """设置模拟响应"""
        self.responses = responses
        
    def send(self, messages: List[Message], **kwargs) -> Union[Message, Generator[str, None, None]]:
        """发送消息"""
        if not self.responses:
            return Message(role="assistant", text="Mock response")
            
        if kwargs.get("stream", False):
            return self._stream_response()
        return Message(role="assistant", text=self.responses.pop(0))
        
    def _stream_response(self):
        """流式响应"""
        response = self.responses.pop(0) if self.responses else "Mock response"
        for char in response:
            yield char
        
    def supports_files(self) -> bool:
        return True
        
    def supports_tools(self) -> bool:
        return True
        
    def get_model_config(self) -> Dict:
        return self.default_kwargs.copy()
        
    def set_model_config(self, config: Dict):
        self.default_kwargs.update(config)

@pytest.fixture
def mock_model():
    model = MockModel()
    return model

@pytest.fixture
def chat_session(mock_model):
    session = ChatSession(default_model=mock_model)
    return session

# 注册 mock 模型
ModelFactory.register_provider(
    "mock",
    model_class=MockModel,
    default_params={
        "temperature": 0.7,
        "stream": False
    }
)

@pytest.fixture
def provider_model():
    class ProviderModel(Model):
        def __init__(self, provider: str = None, **kwargs):
            super().__init__(provider, **kwargs)
            
        def send(self, messages, **kwargs):
            return Message(role="assistant", text="Provider response")
            
        def supports_files(self):
            return True
            
        def supports_tools(self):
            return True
            
        def get_model_config(self):
            return self.default_kwargs.copy()
            
        def set_model_config(self, config):
            self.default_kwargs.update(config)
    return ProviderModel