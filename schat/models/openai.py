import base64
import mimetypes
from typing import List, Dict, Generator, Union, Any
import openai
from .base import Model
from ..core.message import Message

class OpenAIModel(Model):
    """OpenAI模型"""
    
    def __init__(self, provider: str = "openai", **kwargs):
        super().__init__(provider, **kwargs)
        self._supported_file_types = [
            'image/jpeg', 'image/png', 'image/webp'
        ]
        # 确保默认配置包含所有必需字段
        self.default_kwargs = {
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": False,
            "model": "gpt-3.5-turbo"
        }
        self.default_kwargs.update(kwargs)
        
    def _ensure_client(self):
        """确保OpenAI客户端已初始化"""
        if not self.client:
            if not self.api_key:
                # 使用provider名称获取key
                self.api_key = self._key_manager.get_key(self.provider)
            if not self.api_key:
                raise ValueError(f"API key not set and no key available from manager for provider {self.provider}")
                
            client_kwargs = {
                "api_key": self.api_key,
                #**self.default_kwargs  # 添加默认参数
            }
            
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
                
            self.client = openai.OpenAI(**client_kwargs)
            
    def send(self, messages: List[Message], **kwargs) -> Union[Message, Generator[str, None, None]]:
        self._ensure_client()
        
        # 合并参数
        request_kwargs = self.default_kwargs.copy()
        request_kwargs.update(kwargs)
        
        # 转换消息格式
        openai_messages = self._convert_messages(messages)
        
        # 准备请求参数
        api_kwargs = {
            "messages": openai_messages,
            "model": request_kwargs.pop("model", self.default_kwargs["model"]),
            "stream": request_kwargs.pop("stream", False),
        }
        
        # 添加其他参数
        if "tools" in request_kwargs:
            api_kwargs["tools"] = request_kwargs.pop("tools")
        
        # 添加剩余的参数
        api_kwargs.update(request_kwargs)
        
        # 发送请求
        #print(api_kwargs)
        response = self.client.chat.completions.create(**api_kwargs)
        
        if api_kwargs["stream"]:
            return self._handle_stream(response)
        else:
            return self._handle_response(response)
            
    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        """转换息格式为OpenAI API格式"""
        converted = []
        for msg in messages:
            message = {"role": msg.role}
            
            # 处理内容
            if msg.files:
                content = [{"type": "text", "text": msg.text or ""}]
                for file_path in msg.files:
                    content.append({
                        "type": "image_url",
                        "image_url": self.process_file(file_path)
                    })
                message["content"] = content
            else:
                message["content"] = msg.text or ""
                
            # 添加名称（如果有）
            if msg.name:
                message["name"] = msg.name
                
            # 只有在assistant响应中才添加tool_calls
            if msg.role == "assistant" and msg.tool_calls:
                message["tool_calls"] = msg.tool_calls
                
            # 添加工具调用ID（如果有）
            if msg.tool_call_id:
                message["tool_call_id"] = msg.tool_call_id
                
            converted.append(message)
        return converted
        
    def _handle_stream(self, response) -> Generator[str, None, None]:
        """处理流式响应"""
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    def _handle_response(self, response) -> Message:
        """处理普通响应"""
        assistant_message = response.choices[0].message
        
        # 创建助手消息
        message_data = {
            "role": "assistant",
            "text": assistant_message.content or "",
        }
        
        # 处理工具调用
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            tool_calls = []
            for tool_call in assistant_message.tool_calls:
                tool_call_data = {
                    "id": tool_call.id,
                    "type": tool_call.type,
                }
                
                if tool_call.type == "function":
                    tool_call_data["function"] = {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                
                tool_calls.append(tool_call_data)
                
            # 如果有工具调用，将其添加到消息数据中
            message_data["tool_calls"] = tool_calls
            # 如果没有文本内容但有工具调用，设置一个空文本
            if not message_data["text"]:
                message_data["text"] = "Calling function: " + tool_calls[0]["function"]["name"]
        
        return Message(**message_data)
        
    def supports_files(self) -> bool:
        return True
        
    def supports_tools(self) -> bool:
        return True
        
    def process_file(self, file_path: str) -> Dict:
        """处理文件，返回OpenAI API所需的格式"""
        file_type = self.get_file_type(file_path)
        
        if not self.supports_file_type(file_type):
            raise ValueError(f"Unsupported file type: {file_type}")
            
        if self.is_url(file_path):
            return {"url": file_path}
        else:
            return {"url": f"data:image/jpeg;base64,{self.encode_file(file_path)}"}
            
    def supports_file_type(self, file_type: str) -> bool:
        return file_type in self._supported_file_types
        
    def is_url(self, file_path: str) -> bool:
        return file_path.startswith(('http://', 'https://'))
        
    def get_file_type(self, file_path: str) -> str:
        if self.is_url(file_path):
            return mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        else:
            return mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
    def encode_file(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def get_model_config(self) -> Dict:
        """获取模型配置"""
        return {
            "temperature": self.default_kwargs["temperature"],
            "max_tokens": self.default_kwargs["max_tokens"],
            "stream": self.default_kwargs["stream"],
            "model": self.default_kwargs["model"]
        }
        
    def _prepare_request_kwargs(self, **kwargs) -> Dict:
        """准备请求参数"""
        request_kwargs = {
            "messages": self._convert_messages(kwargs.get("messages", [])),
            "model": kwargs.get("model", self.default_kwargs["model"]),
            "stream": kwargs.get("stream", False),
        }
        
        # 添加工具支持
        if "tools" in kwargs:
            request_kwargs["tools"] = kwargs["tools"]
        
        # 添加其他参数
        for key, value in kwargs.items():
            if key not in ["messages", "tools"]:
                request_kwargs[key] = value
                
        return request_kwargs
        
    def _send_llm(self, **kwargs) -> Any:
        """发送请求到OpenAI API"""
        return self.client.chat.completions.create(**kwargs)