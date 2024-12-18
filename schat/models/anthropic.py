from typing import List, Dict, Generator, Union, Any
import anthropic
from .base import Model
from ..core.message import Message
import base64
import json
import requests
from .anthropic_helper import add_cache_to_messages

class AnthropicModel(Model):
    """Anthropic模型实现"""
    
    def __init__(self, provider: str = "anthropic", **kwargs):
        super().__init__(provider, **kwargs)
        
        
    def _ensure_client(self):
        """确保Anthropic API客户端已初始化"""
        if not self.client:
            if not self.api_key:
                self.api_key = self._key_manager.get_key(self.provider)
            if not self.api_key:
                raise ValueError(f"API key not set and no key available from manager for provider {self.provider}")
                
            # 只使用 api_key 初始化客户端
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def _download_image(self, url: str) -> bytes:
        """从URL下载图片
        
        Args:
            url: 图片URL
            
        Returns:
            bytes: 图片数据
            
        Raises:
            ValueError: 下载失败
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise ValueError(f"Failed to download image from {url}: {e}")

    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        """转换消息格式为Anthropic API格式"""
        converted = []
        last_was_tool_use = False
        
        for msg in messages:
            content = []
            
            # 添加文本内容
            if msg.text:
                content.append({"type": "text", "text": msg.text})
                
            # 添加文件内容
            if msg.files:
                for file_path in msg.files:
                    file_type = self.get_file_type(file_path)
                    if not self.supports_file_type(file_type):
                        raise ValueError(f"Unsupported file type: {file_type}")
                    
                    # 处理图片
                    if file_type.startswith('image/'):
                        if self.is_url(file_path):
                            # 下载URL图片并转换为base64
                            image_data = self._download_image(file_path)
                            base64_data = base64.b64encode(image_data).decode('utf-8')
                            content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": file_type,
                                    "data": base64_data
                                }
                            })
                        else:
                            with open(file_path, 'rb') as f:
                                base64_data = base64.b64encode(f.read()).decode('utf-8')
                                content.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": file_type,
                                        "data": base64_data
                                    }
                                })
                    # 处理文档
                    else:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content.append({
                                "type": "text",
                                "text": f.read()
                            })
            
            # 处理工具调用
            if msg.role == "assistant" and hasattr(msg, 'content') and msg.content:
                # 如果消息中有 content 字段（包含 tool_use block），直接使用
                content = msg.content
                last_was_tool_use = True
            elif msg.role == "tool" and msg.tool_call_id:
                if not last_was_tool_use:
                    continue
                
                message = {
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.text
                    }]
                }
                converted.append(message)
                continue
            
            message = {"role": msg.role, "content": content}
            converted.append(message)
            
            # 更新 last_was_tool_use 标志
            if msg.role == "assistant" and msg.tool_calls:
                last_was_tool_use = True
            else:
                last_was_tool_use = False
        
        return converted
        
    def _prepare_request_kwargs(self, **kwargs) -> Dict:
        """准备请求参数"""
        request_kwargs = {
            "model": kwargs.get("model", "claude-3-opus-20240229"),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": kwargs.get("stream", False),
            "extra_headers": {
                "anthropic-beta": "prompt-caching-2024-07-31"
            }
        }
        
        # 转换消息格式并添加到请求参数中
        messages = kwargs.get("messages", [])
        if messages:
            anthropic_messages = self._convert_messages(messages)
            request_kwargs["messages"] = add_cache_to_messages(anthropic_messages)
            
            # 检查是否需要包含工具定义
            tools = kwargs.get("tools", [])
            needs_tools = tools is not None
            
            # 如果历史消息中包含工具相关内容，就需要包含工具定义
            for msg in messages:
                if (hasattr(msg, 'content') and msg.content and 
                    any(c.get('type') in ['tool_use', 'tool_result'] for c in msg.content)):
                    needs_tools = True
                    break
                if msg.tool_calls or msg.tool_call_id:
                    needs_tools = True
                    break
            
            if needs_tools:
                # 如果没有提供工具定义，尝试从历史消息中获取
                if not tools:
                    for msg in messages:
                        if msg.role == "assistant" and msg.tool_calls:
                            # 从工具调用中重建工具定义
                            for tool_call in msg.tool_calls:
                                if tool_call["type"] == "function":
                                    tools.append({
                                        "type": "function",
                                        "function": {
                                            "name": tool_call["function"]["name"],
                                            "parameters": {
                                                "type": "object",
                                                "properties": {}  # 简化的参数定义
                                            }
                                        }
                                    })
                
                # 转换并添加工具定义到请求参数
                if tools:
                    request_kwargs["tools"] = self._convert_tools(tools)
        
        return request_kwargs

    def _send_llm(self, **kwargs) -> Any:
        """发送请求到Anthropic API"""
        return self.client.messages.create(**kwargs)
        
    def _handle_stream(self, response) -> Generator[str, None, None]:
        for chunk in response:
            if chunk.delta.text:
                yield chunk.delta.text
                
    def _handle_response(self, response) -> Message:
        """处理响应"""
        # 检查是否有工具调用
        if response.stop_reason == "tool_use":
            # 找到工具调用内容
            tool = next(c for c in response.content if c.type == "tool_use")
            tool_calls = [{
                "id": tool.id,
                "type": "function",
                "function": {
                    "name": tool.name,
                    "arguments": json.dumps(tool.input)
                }
            }]
            
            # 返回包含 tool_use block 的消息
            return Message(
                role="assistant",
                text="",  # 不需要文本内容
                tool_calls=tool_calls,
                content=[{
                    "type": "tool_use",
                    "id": tool.id,
                    "name": tool.name,
                    "input": tool.input
                }]
            )
        
        # 处理普通响应
        text_content = []
        for content in response.content:
            if content.type == "text":
                text_content.append(content.text)
        
        return Message(
            role="assistant",
            text="".join(text_content)
        )
        
    def supports_files(self) -> bool:
        return True
        
    def supports_tools(self) -> bool:
        return True 
        
    def get_model_config(self) -> Dict:
        """获取模型配置"""
        return {
            "temperature": self.default_kwargs["temperature"],
            "max_tokens": self.default_kwargs["max_tokens"],
            "stream": self.default_kwargs["stream"],
            "model": self.default_kwargs["model"]
        }
        
    def set_model_config(self, config: Dict):
        """设置模型配置
        
        注意：Anthropic模型的配置在每次请求时生效，而不是在客户端初始化时
        """
        # 保存配置以供后续使用
        self.default_kwargs = config
        
    def _convert_tools(self, tools: List[Dict]) -> List[Dict]:
        """转换工具定义为Anthropic格式"""
        converted = []
        for tool in tools:
            if tool["type"] == "function":
                func = tool["function"]
                converted.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": {
                        "type": "object",
                        "properties": func["parameters"]["properties"],
                        "required": func["parameters"].get("required", [])
                    }
                })
        return converted