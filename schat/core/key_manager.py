import os
from typing import Dict, List, Optional
import random
import hashlib
from threading import Lock

class APIKeyManager:
    """API密钥管理器"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._provider_keys: Dict[str, List[str]] = {}  # provider -> [keys]
            self._key_counts: Dict[str, Dict[str, int]] = {}  # provider -> {key -> count}
            self._current_seed: Optional[str] = None
            self._initialized = True
    
    def load_keys_from_env(self, provider_name: str) -> bool:
        """从环境变量加载API密钥
        
        环境变量格式：
        - 单个key: PROVIDER_KEY=xxx
        - 多个key: PROVIDER_KEY=key1,key2,key3
        
        Args:
            provider_name: 提供者名称，会自动转大写并添加_KEY后缀
            
        Returns:
            bool: 是否成功加载了key
        """
        env_name = f"{provider_name.upper()}_KEY"
        keys_str = os.getenv(env_name)
        
        if not keys_str:
            return False
            
        # 分割并清理key
        keys = [k.strip() for k in keys_str.split(',') if k.strip()]
        if not keys:
            return False
            
        self._provider_keys[provider_name] = keys
        self._key_counts[provider_name] = {k: 0 for k in keys}
        return True
    
    def add_key(self, provider_name: str, key: str):
        """添加单个API密钥"""
        if provider_name not in self._provider_keys:
            self._provider_keys[provider_name] = []
            self._key_counts[provider_name] = {}
            
        if key not in self._provider_keys[provider_name]:
            self._provider_keys[provider_name].append(key)
            self._key_counts[provider_name][key] = 0
    
    def set_current_seed_once(self, seed: str):
        """设置一次性seed，用于下次获取key
        
        下次获取key后seed会被清除
        """
        self._current_seed = seed
    
    def get_key(self, provider_name: str) -> Optional[str]:
        """获取API密钥
        
        如果设置了seed，则使用seed确定key；
        否则使用负载均衡策略选择使用次数最少的key
        
        Args:
            provider_name: 提供者名称
            
        Returns:
            str: API密钥，如果没有可用的密钥则返回None
        """
        if provider_name not in self._provider_keys:
            self.load_keys_from_env(provider_name)
            
        keys = self._provider_keys.get(provider_name, [])
        if not keys:
            return None
            
        selected_key = None
        
        # 如果设置了seed，使用seed选择key
        if self._current_seed is not None:
            # 使用seed和provider_name生成hash
            hash_input = f"{self._current_seed}:{provider_name}"
            hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
            selected_key = keys[hash_value % len(keys)]
            self._current_seed = None  # 清除seed
        else:
            # 使用负载均衡策略
            counts = self._key_counts[provider_name]
            min_count = min(counts.values())
            min_keys = [k for k, c in counts.items() if c == min_count]
            selected_key = random.choice(min_keys)
            
        # 增加使用计数
        self._key_counts[provider_name][selected_key] += 1
        return selected_key
    
    def get_key_counts(self, provider_name: str) -> Dict[str, int]:
        """获取指定提供者的key使用计数"""
        return self._key_counts.get(provider_name, {}).copy()
    
    def clear_counts(self, provider_name: Optional[str] = None):
        """清除使用计数
        
        Args:
            provider_name: 指定提供者名称，如果为None则清除所有计数
        """
        if provider_name:
            if provider_name in self._key_counts:
                self._key_counts[provider_name] = {k: 0 for k in self._key_counts[provider_name]}
        else:
            for provider in self._key_counts:
                self._key_counts[provider] = {k: 0 for k in self._key_counts[provider]} 