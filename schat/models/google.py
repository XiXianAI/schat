from typing import List, Dict, Generator, Union, Any
import time
import google.generativeai as genai
from .base import Model
from ..core.message import Message
import json

class GoogleModel(Model):
    """Google Gemini模型实现"""
    
    
    def __init__(self, provider: str = "google", **kwargs):
        super().__init__(provider, **kwargs)
        self._supported_file_types = [
            # 图片类型
            'image/jpeg',
            'image/png',
            'image/webp',

            # 视频类型
            'video/mp4',
            'video/webm',
            'video/ogg',
            'video/quicktime',  # MOV
            'video/x-msvideo',  # AVI
            'video/mpeg', #MPEG

            # 文档类型
            'text/plain',       # TXT
            'text/html',       # HTML
            'text/css',        # CSS
            'application/javascript',  # JS
            'application/json',     # JSON
            'application/xml',  # XML
            'text/xml',  # XML
            'application/pdf',      # PDF
            'application/msword',   # DOC
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document', # DOCX
            'application/vnd.ms-excel', # XLS
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', # XLSX
            'application/vnd.ms-powerpoint',  # PPT
            'application/vnd.openxmlformats-officedocument.presentationml.presentation', # PPTX
            'text/markdown', # MD
            'text/x-markdown' #MD
        ]
        self._file_cache: Dict[str, object] = {}
    
        
    def _ensure_client(self):
        """确保Google API客户端已初始化"""
        if not self.client:
            if not self.api_key:
                self.api_key = self._key_manager.get_key(self.provider)
            if not self.api_key:
                raise ValueError(f"API key not set and no key available from manager for provider {self.provider}")
                
            # 配置Google API
            genai.configure(api_key=self.api_key)
            
            # 创建生成配置
            generation_config = {
                "temperature": self.default_kwargs["temperature"],
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": self.default_kwargs["max_tokens"],
            }
            
            # 创建模型实例
            self.client = genai.GenerativeModel(
                model_name=self.default_kwargs["model"],
                generation_config=generation_config
            )
            
    def _wait_for_file_active(self, file_obj):
        """等待文件处理完��并变为可用状态
        
        Args:
            file_obj: Google API上传的文件对象
            
        Raises:
            Exception: 如果文件处理失败
        """
        print(f"等待文件 {file_obj.name} 处理中...")
        while True:
            file = genai.get_file(file_obj.name)
            if file.state.name == "ACTIVE":
                break
            elif file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(1)  # 每1秒检查一次
            else:
                raise Exception(f"文件 {file.name} 处理失败: {file.state.name}")
        print(f"\n文件 {file_obj.name} 处理完成")
        
    def _wait_for_files_active(self, files):
        """等待多个文件处理完成
        
        Args:
            files: 文件对象列表
        """
        for file in files:
            self._wait_for_file_active(file)
            
    def _upload_file(self, file_path: str, mime_type: str) -> object:
        """上传文件到Google API，带缓存功能
        
        Args:
            file_path: 文件路径
            mime_type: MIME类型
            
        Returns:
            object: Google API的文件对象
        """
        # 生成缓存键
        cache_key = f"{file_path}:{mime_type}"
        
        # 检查缓存
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]
            
        # 上传文件
        print(f'正在上传文件: {file_path} ({mime_type})')
        file = genai.upload_file(file_path, mime_type=mime_type)
        print(f"文件已上传: {file.display_name} -> {file.uri}")
        
        # 等待文件处理完成
        self._wait_for_file_active(file)
        
        # 缓存结果
        self._file_cache[cache_key] = file
        
        return file
            
    def _convert_tool_to_function_declarations(self, tools: List[Dict]) -> List[Dict]:
        """转换工具定义为Gemini的function declarations格式"""
        declarations = []
        for tool in tools:
            if tool["type"] == "function":
                func = tool["function"]
                # 转换参数格式
                parameters = {
                    "type": "OBJECT",  # 必须指定顶层类型为OBJECT
                    "properties": {}
                }
                
                for name, prop in func["parameters"]["properties"].items():
                    param_type = prop.get("type", "string").upper()
                    if param_type == "string":
                        param_type = "STRING"
                    elif param_type == "number":
                        param_type = "NUMBER"
                    elif param_type == "integer":
                        param_type = "INTEGER"
                    elif param_type == "boolean":
                        param_type = "BOOLEAN"
                    
                    parameters["properties"][name] = {
                        "type": param_type,
                        "description": prop.get("description", "")
                    }
                    if "enum" in prop:
                        parameters["properties"][name]["enum"] = prop["enum"]
                
                if "required" in func["parameters"]:
                    parameters["required"] = func["parameters"]["required"]

                declaration = {
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "parameters": parameters
                }
                declarations.append(declaration)
        return declarations
        
    def _convert_messages(self, messages: List[Message]) -> List[Dict]:
        """转换消息格式为Google API格式"""
        converted = []
        uploaded_files = []
        
        for msg in messages:
            parts = []
            
            # 添加文本内容
            if msg.text:
                parts.append(msg.text)
                
            # 添加文件内容
            if msg.files:
                for file_path in msg.files:
                    # 检查文件类型
                    file_type = self.get_file_type(file_path)
                    if not self.supports_file_type(file_type):
                        raise ValueError(f"Unsupported file type: {file_type}")
                        
                    # 上传文件到Google API（使用缓存）
                    file = self._upload_file(file_path, file_type)
                    parts.append(file)
                    uploaded_files.append(file)
                    
            # 处理工具调用结果
            if msg.role == "tool" and msg.tool_call_id:
                parts = [f"Function response for {msg.tool_call_id}: {msg.text}"]
                
            message = {
                "role": "user" if msg.role == "user" else "model",
                "parts": parts
            }
            converted.append(message)
            
        return converted
        
    def clear_file_cache(self):
        """清除文件缓存"""
        self._file_cache.clear()
        
    def remove_file_from_cache(self, file_path: str):
        """从缓存中移除指定文件
        
        Args:
            file_path: 文件路径
        """
        keys_to_remove = [
            key for key in self._file_cache.keys()
            if key.startswith(f"{file_path}:")
        ]
        for key in keys_to_remove:
            del self._file_cache[key]
            
    def send(self, messages: List[Message], **kwargs) -> Union[Message, Generator[str, None, None]]:
        """发送消息到模型并获取响应"""
        self._ensure_client()
        
        # 合并参数
        request_kwargs = self.default_kwargs.copy()
        request_kwargs.update(kwargs)
        
        # 转换消息格式
        google_messages = self._convert_messages(messages)
        
        # 创建或获取聊天会话
        chat = self.client.start_chat(history=google_messages[:-1])
        
        # 处理工具调用
        tools = kwargs.get("tools", [])
        if tools:
            function_declarations = self._convert_tool_to_function_declarations(tools)
            response = chat.send_message(
                google_messages[-1]["parts"],
                tools=[{
                    "function_declarations": function_declarations
                }],
                stream=request_kwargs.get("stream", False)
            )
        else:
            response = chat.send_message(
                google_messages[-1]["parts"],
                stream=request_kwargs.get("stream", False)
            )
        
        if request_kwargs.get("stream"):
            return self._handle_stream(response)
        else:
            return self._handle_response(response)
            
    def _handle_stream(self, response) -> Generator[str, None, None]:
        """处理流式响应"""
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    def _handle_response(self, response) -> Message:
        """处理普通响应"""
        # 检查是否有函数调用
        if hasattr(response, 'candidates') and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                
                # 检查 args 是否存在且不为 None
                if hasattr(function_call, 'args') and function_call.args is not None:
                    args_dict = {}
                    try:
                        # 如果已经是字典类型
                        if isinstance(function_call.args, dict):
                            args_dict = function_call.args
                        # 如果是其他可迭代类型
                        elif hasattr(function_call.args, 'items'):
                            for key, value in function_call.args.items():
                                args_dict[key] = value
                        else:
                            args_dict = {"raw_args": str(function_call.args)}
                    except Exception as e:
                        args_dict = {"error": str(e)}
                    
                    tool_calls = [{
                        "id": f"call_{hash(function_call.name)}",
                        "type": "function",
                        "function": {
                            "name": function_call.name,
                            "arguments": json.dumps(args_dict)
                        }
                    }]
                    return Message(
                        role="assistant",
                        text=f"Calling function: {function_call.name}",
                        tool_calls=tool_calls
                    )
        
        # 如果没有函数调用或处理失败，返回普通响应
        return Message(
            role="assistant",
            text=response.text if hasattr(response, 'text') else str(response)
        )
        
    def supports_files(self) -> bool:
        """是否支持文件输入"""
        return True
        
    def supports_tools(self) -> bool:
        """是否支持工具调用"""
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
        """设置模型配置"""
        self.default_kwargs.update(config)
        # 如果客户端已存在,更新配置
        if self.client:
            self.client.generation_config.update({
                "temperature": config.get("temperature", self.default_kwargs["temperature"]),
                "max_output_tokens": config.get("max_tokens", self.default_kwargs["max_tokens"])
            }) 

    def _prepare_request_kwargs(self, **kwargs) -> Dict:
        """准备请求参数"""
        request_kwargs = self.default_kwargs.copy()
        request_kwargs.update(kwargs)
        
        # 转换消息格式
        messages = self._convert_messages(kwargs.get("messages", []))
        
        # 创建聊天会话
        chat = self.client.start_chat(history=messages[:-1])
        request_kwargs["chat"] = chat
        request_kwargs["message"] = messages[-1]["parts"]
        
        # 处理工具调用
        if "tools" in kwargs:
            request_kwargs["tools"] = [{
                "function_declarations": self._convert_tool_to_function_declarations(kwargs["tools"])
            }]
        
        return request_kwargs

    def _send_llm(self, **kwargs) -> Any:
        """发送请求到Google API"""
        chat = kwargs.pop("chat")
        message = kwargs.pop("message")
        return chat.send_message(message, **kwargs)