from typing import Dict, List
import openai
from .openai import OpenAIModel
from .anthropic_helper import add_cache_to_messages
from ..core.message import Message

class OpenRouterModel(OpenAIModel):
    """OpenRouter模型实现，支持多种模型包括Anthropic的Claude"""
    
    def __init__(self, provider: str = "openrouter", **kwargs):
        super().__init__(provider, **kwargs)
        self.base_url = "https://openrouter.ai/api/v1"
        
    def _is_claude_model(self, model: str) -> bool:
        """检查是否是Claude模型"""
        return "claude" in model.lower()
        
    def before_send(self, messages: List[Message], request_kwargs: Dict) -> Dict:
        """在发送前处理消息和参数"""
        model = request_kwargs.get("model", self.default_kwargs.get("model", ""))
        
        # 如果是Claude模型，添加缓存支持
        if self._is_claude_model(model):
            # 添加Anthropic缓存header
            request_kwargs.setdefault("extra_headers", {}).update({
                "anthropic-beta": "prompt-caching-2024-07-31"
            })
            
            # 如果有消息，添加缓存控制
            if "messages" in request_kwargs:
                request_kwargs["messages"] = add_cache_to_messages(request_kwargs["messages"])
        
        return request_kwargs
    
    def _create_client(self, **kwargs) -> openai.OpenAI:
        """创建OpenAI客户端"""
        return openai.OpenAI(**kwargs)
    
    def _ensure_client(self):
        """确保OpenRouter客户端已初始化"""
        if not self.client:
            if not self.api_key:
                self.api_key = self._key_manager.get_key(self.provider)
            if not self.api_key:
                raise ValueError(f"API key not set and no key available from manager for provider {self.provider}")
            
            client_kwargs = {
                "api_key": self.api_key,
                "base_url": self.base_url
            }
            
            self.client = self._create_client(**client_kwargs)