from abc import ABC, abstractmethod
from typing import List, Dict, Generator, Union, Any
import mimetypes
from ..core.message import Message
from ..core.key_manager import APIKeyManager

class Model(ABC):
    """模型的抽象基类，同时也是Provider"""
    
    def __init__(self, provider: str = None, **kwargs):
        self.provider = provider  # 当前provider名称
        self.api_key: str = None
        self.base_url: str = None
        self._supported_models: List[str] = []  # 空列表表示不限制模型
        self._supported_file_types: List[str] = []
        self.default_kwargs = kwargs.copy()
        self.client = None
        self._key_manager = APIKeyManager()
        
    def set_api_key(self, api_key: str):
        """设置API密钥"""
        self.api_key = api_key
        
    def set_base_url(self, base_url: str):
        """设置API基础URL"""
        self.base_url = base_url
        
    def send(self, messages: List[Message], **kwargs) -> Union[Message, Generator[str, None, None]]:
        """发送消息到模型并获取响应 (模板方法)"""
        self._ensure_client()
        
        # 准备请求参数，确保传入消息
        request_kwargs = self._prepare_request_kwargs(messages=messages, **kwargs)
        
        # 在发送前处理消息和参数
        request_kwargs = self.before_send(messages, request_kwargs)
        
        # 发送请求并获取响应
        response = self._send_llm(**request_kwargs)
        
        # 处理响应
        if request_kwargs.get("stream", False):
            return self._handle_stream(response)
        else:
            return self._handle_response(response)
    
    def before_send(self, messages: List[Message], request_kwargs: Dict) -> Dict:
        """在发送前处理消息和参数，子类可以重写此方法"""
        return request_kwargs
    
    @abstractmethod
    def _send_llm(self, **kwargs) -> Any:
        """实际发送请求到LLM的方法"""
        pass
    
    @abstractmethod
    def _prepare_request_kwargs(self, **kwargs) -> Dict:
        """准备请求参数"""
        pass
    
    @abstractmethod
    def _ensure_client(self):
        """确保客户端已初始化"""
        pass
    
    @abstractmethod
    def _handle_stream(self, response) -> Generator[str, None, None]:
        """处理流式响应"""
        pass
    
    @abstractmethod
    def _handle_response(self, response) -> Message:
        """处理普通响应"""
        pass
    
    def supports_model(self, model: str) -> bool:
        """检查是否支持指定的模型"""
        return not self._supported_models or model in self._supported_models
        
    def supports_files(self) -> bool:
        """是否支持文件输入"""
        return False
        
    def supports_tools(self) -> bool:
        """是否支持工具调用"""
        return False
        
    def get_model_config(self) -> Dict:
        """获取模型配置"""
        return self.default_kwargs.copy()
        
    def set_model_config(self, config: Dict):
        """设置模型配置"""
        self.default_kwargs.update(config)

    def get_file_type(self, file_path: str) -> str:
        """获取文件的MIME类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: MIME类型，如 'image/jpeg'
        """
        mime_type = mimetypes.guess_type(file_path)[0]
        if not mime_type:
            # 如果无法判断类型，返回二进制流类型
            return 'application/octet-stream'
        return mime_type
        
    def supports_file_type(self, file_type: str) -> bool:
        """检查是否支持指定的文件类型
        
        Args:
            file_type: MIME类型
            
        Returns:
            bool: 是否支持该文件类型
        """
        # 如果没有指定支持的文件类型，则默认支持所有类型
        return not self._supported_file_types or file_type in self._supported_file_types
        
    def is_url(self, file_path: str) -> bool:
        """检查是否是URL
        
        Args:
            file_path: 文件路径或URL
            
        Returns:
            bool: 是否是URL
        """
        return file_path.startswith(('http://', 'https://'))
 