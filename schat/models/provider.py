from typing import Dict, Type, Optional
from .base import Model
from ..config import DEFAULT_PROVIDERS
import importlib

class ProviderManager:
    """Provider管理类"""
    
    _instance = None
    _providers: Dict[str, Dict] = {}  # 存储provider的完整配置
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 注册默认的providers
            cls._instance._register_defaults()
        return cls._instance
    
    def _register_defaults(self):
        """注册默认的providers"""
        for provider, config in DEFAULT_PROVIDERS.items():
            try:
                self.register_provider(provider, config)
            except ValueError:
                # 如果模型类不存在，跳过注册
                continue
    
    def register_provider(self, provider: str, config: Dict):
        """注册provider
        
        Args:
            provider: provider名称
            config: provider配置，包含class、base_url等信息
            
        Raises:
            ValueError: 配置无效或模型类加载失败
        """
        try:
            self._providers[provider] = config.copy()
            
            # 如果配置中包含模型类，尝试加载
            if "class" in config:
                class_name = config["class"]
                if isinstance(class_name, str):
                    # 动态导入模型类
                    try:
                        # 从 schat.models 包中导入
                        module = importlib.import_module("..models", package="schat.models")
                        ModelClass = getattr(module, class_name)
                        
                        # 验证是否是 Model 的子类
                        if not issubclass(ModelClass, Model):
                            raise ValueError(f"Class {class_name} is not a subclass of Model")
                            
                        self._providers[provider]["model_class"] = ModelClass
                        
                    except (ImportError, AttributeError) as e:
                        # 如果导入失败，尝试检查是否需要额外的依赖
                        if "google" in class_name.lower():
                            try:
                                import google.generativeai
                                from .google import GoogleModel as ModelClass
                                self._providers[provider]["model_class"] = ModelClass
                            except ImportError:
                                raise ImportError(
                                    "Google Generative AI package not installed. "
                                    "Please install it with: pip install google-generativeai"
                                )
                        else:
                            raise ValueError(f"Failed to load model class {class_name}: {e}")
                else:
                    # 如果class不是字符串，假设是直接的类引用
                    self._providers[provider]["model_class"] = class_name
                    
        except Exception as e:
            # 如果发生任何错误，移除配置
            if provider in self._providers:
                del self._providers[provider]
            raise ValueError(f"Failed to register provider {provider}: {e}")
    
    def get_provider_config(self, provider: str) -> Dict:
        """获取provider的完整配置"""
        if provider not in self._providers:
            raise ValueError(f"Unknown provider: {provider}")
        return self._providers[provider]