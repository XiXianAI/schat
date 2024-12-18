from typing import List, Dict, Optional, Union, Generator, Any
from dataclasses import asdict
import json
from .message import Message
from ..models.factory import ModelFactory
from ..models.base import Model

class ChatSession:
    """聊天会话管理类"""
    
    def __init__(self, 
                 default_model: Union[str, Model, None] = None,
                 stream: bool = False,
                 max_history_token: int = 0):
        self.history: List[Message] = []
        self.default_model = default_model
        self.system_prompt: Optional[str] = None
        self.max_history_token = max_history_token
        self.stream = stream
        
    def set_system_prompt(self, text: str):
        """设置系统提示"""
        self.system_prompt = text
        
    def add_user_message(self, 
                        text: str,
                        files: Optional[List[str]] = None,
                        tools: Optional[List[Dict]] = None,
                        priority: float = 1.0) -> Message:
        """添加用户消息"""
        msg = Message(
            role="user",
            text=text,
            files=files or [],
            tool_calls=tools or [],
            priority=priority
        )
        self.add_message(msg)
        return msg
        
    def add_assistant_message(self, 
                            text: str,
                            tool_calls: Optional[List[Dict]] = None,
                            priority: float = 1.0) -> Message:
        """添加助手消息"""
        msg = Message(
            role="assistant",
            text=text,
            tool_calls=tool_calls or [],
            priority=priority
        )
        self.add_message(msg)
        return msg
        
    def add_message(self, message: Message):
        """添加消息到历史记录"""
        self.history.append(message)
        
    def send(self,
             text: str,
             model: Union[str, Model, None] = None,
             files: Optional[List[str]] = None,
             tools: Optional[List[Dict]] = None,
             priority: float = 1.0,
             stream: Optional[bool] = None,
             **kwargs) -> Union[Message, Generator[str, None, None]]:
        """发送消息并获取响应"""
        # 获取当前模型
        current_model = self._get_model(model)
        
        # 创建用户消息（包含tools）
        user_message = Message(
            role="user",
            text=text,
            files=files,
            tool_calls=tools,
            priority=priority
        )
        self.add_message(user_message)
        
        # 准备发送给模型的参数
        model_kwargs = kwargs.copy()
        
        # 添加特殊参数
        if tools is not None:
            model_kwargs["tools"] = tools
        if stream is None:
            stream = self.stream
        if stream:
            model_kwargs["stream"] = True
        
        # 获取历史消息
        history = self._get_history()
        
        # 发送给模型
        response = current_model.send(history, **model_kwargs)
        
        # 处理响应
        if isinstance(response, Generator):
            return response
        else:
            self.add_message(response)
            return response
        
    def _prepare_messages(self) -> List[Message]:
        """准备发送给模型的消息列表"""
        messages = []
        if self.system_prompt:
            messages.append(Message(role="system", text=self.system_prompt))
        messages.extend(self.history)
        return messages
        
    def save(self, path: str):
        """保存会话到文件"""
        data = {
            "system_prompt": self.system_prompt,
            "history": [
                {
                    "role": msg.role,
                    "text": msg.text,
                    "priority": msg.priority,
                    "files": msg.files,
                    "timestamp": msg.timestamp,
                    "tool_calls": msg.tool_calls,
                    "tool_call_id": msg.tool_call_id,
                    "name": msg.name
                } for msg in self.history
            ],
            "max_history_token": self.max_history_token,
            "stream": self.stream,
            "default_model": self._serialize_model(self.default_model)
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def _serialize_model(self, model: Union[str, Model, None]) -> Optional[str]:
        """序列化模型对象"""
        if isinstance(model, Model):
            # 保存模型的类名和配置
            return {
                "type": model.__class__.__name__,
                "config": model.get_model_config()
            }
        return model
        
    def _deserialize_model(self, data: Union[str, Dict, None]) -> Optional[Union[str, Model]]:
        """反序列化模型对象"""
        if not data:
            return None
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            # 根据类型创建模型实例
            model_type = data["type"]
            config = data.get("config", {})
            
            # 从已注册的模型中查找
            for provider, model_class in ModelFactory._models.items():
                if model_class.__name__ == model_type:
                    model = model_class()
                    model.set_model_config(config)
                    return model
        return None
        
    def load(self, path: str):
        """从文件加载会话"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.system_prompt = data["system_prompt"]
        self.max_history_token = data["max_history_token"]
        self.stream = data.get("stream", False)
        self.default_model = self._deserialize_model(data["default_model"])
        self.history = [Message(**msg) for msg in data["history"]]
        
    def get_current_round(self) -> int:
        """获取当前轮次"""
        return len(self.history) // 2
        
    def truncate_history(self, n: int):
        """保留最近n轮对话"""
        if n * 2 < len(self.history):
            self.history = self.history[-n*2:]
            
    def set_priority(self, round_num: int, priority: float):
        """设置某轮对话的优先级"""
        if 0 <= round_num < self.get_current_round():
            idx = round_num * 2
            self.history[idx].priority = priority
            self.history[idx + 1].priority = priority 
        
    def add_tool_message(self, tool_result: Any, tool_call_id: str):
        """添加工具调用结果消息
        
        Args:
            tool_result: 工具调用的结果，可以是字符串或其他类型
            tool_call_id: 工具调用的ID，用于关联请求和响应
        
        Returns:
            Message: 创建的工具消息
        """
        if isinstance(tool_result, str):
            content = tool_result
        else:
            content = json.dumps(tool_result)
            
        # 创建工具消息
        message = Message(
            role="tool",
            text=content,
            tool_call_id=tool_call_id
        )
        self.add_message(message)
        return message
        
    def _get_model(self, model: Union[str, Model, None] = None) -> Model:
        """获取模型实例
        
        Args:
            model: 可以是模型实例、模型名称字符串或None（使用默认模型）
            
        Returns:
            Model: 模型实例
            
        Raises:
            ValueError: 当没有指定模��且没有默认模型时
        """
        if isinstance(model, Model):
            return model
        
        use_model = model or self.default_model
        if not use_model:
            raise ValueError("No model specified and no default model set")
        
        if isinstance(use_model, Model):
            return use_model
        
        return ModelFactory.get_model(use_model)
        
    def _get_history(self) -> List[Message]:
        """获取历史消息列表
        
        Returns:
            List[Message]: 历史消息列表，如果有系统提示会添加到开头
        """
        history = self.history.copy()
        if self.system_prompt:
            history.insert(0, Message(role="system", text=self.system_prompt))
        return history