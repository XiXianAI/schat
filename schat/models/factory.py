from typing import Dict, Type, Union, Optional
from .base import Model
from .provider import ProviderManager

class ModelFactory:
    """模型工厂类"""
    
    _instances: Dict[str, Model] = {}
    _provider_manager = ProviderManager()
    _models: Dict[str, Type[Model]] = {}
    
    @classmethod
    def register_provider(cls, 
                         provider: str, 
                         model_class: Optional[Type[Model]] = None, 
                         base_url: Optional[str] = None,
                         openai_compatible: bool = False,
                         default_params: Optional[Dict] = None):
        """注册provider"""
        config = {
            "class": model_class if model_class else "OpenAIModel",
            "base_url": base_url,
            "openai_compatible": openai_compatible,
            "default_params": default_params or {}
        }
        cls._provider_manager.register_provider(provider, config)
        if model_class:
            cls._models[provider] = model_class
            
    @classmethod
    def get_model(cls, model_string: str, **kwargs) -> Model:
        """获取模型实例"""
        if ":" in model_string:
            provider, model_name = model_string.split(":", 1)
        else:
            provider = model_string
            model_name = None
            
        model_key = model_string
        
        if model_key not in cls._instances:
            # 获取provider配置
            provider_config = cls._provider_manager.get_provider_config(provider)
            
            # 创建实例
            model_class = provider_config["model_class"]
            instance = model_class(provider=provider)  # 传入provider名称
            
            # 设置base_url(如果有)
            if provider_config.get("base_url"):
                instance.set_base_url(provider_config["base_url"])
            
            # 合并配置参数
            config = provider_config.get("default_params", {}).copy()
            # 设置用户传入的参数（优先级更高）
            config.update(kwargs)  # 移到这里，让用户参数覆盖默认参数
            if model_name:
                config["model"] = model_name
                
            # 设置默认参数和用户参数
            instance.set_model_config(config)
            cls._instances[model_key] = instance
        else:
            # 如果实例已存在但有新的配置参数，更新配置
            if kwargs:
                cls._instances[model_key].set_model_config(kwargs)
        
        return cls._instances[model_key]
        
    @classmethod
    def set_model_config(cls, model_string: str, config: Dict):
        """设置模型配置"""
        if model_string in cls._instances:
            cls._instances[model_string].set_model_config(config)