import pytest
import os
from schat.core.key_manager import APIKeyManager

@pytest.fixture
def key_manager():
    manager = APIKeyManager()
    # 清理现有的keys和counts
    manager._provider_keys = {}
    manager._key_counts = {}
    manager._current_seed = None
    return manager

def test_singleton():
    manager1 = APIKeyManager()
    manager2 = APIKeyManager()
    assert manager1 is manager2

def test_load_keys_from_env(key_manager, monkeypatch):
    # 测试单个key
    monkeypatch.setenv('OPENAI_KEY', 'test-key')
    assert key_manager.load_keys_from_env('openai')
    assert key_manager._provider_keys['openai'] == ['test-key']
    
    # 测试多个key
    monkeypatch.setenv('ANTHROPIC_KEY', 'key1,key2,key3')
    assert key_manager.load_keys_from_env('anthropic')
    assert len(key_manager._provider_keys['anthropic']) == 3
    
    # 测试空环境变量
    monkeypatch.delenv('OPENAI_KEY', raising=False)
    assert not key_manager.load_keys_from_env('openai')

def test_add_key(key_manager):
    key_manager.add_key('test', 'key1')
    assert 'test' in key_manager._provider_keys
    assert key_manager._provider_keys['test'] == ['key1']
    assert key_manager._key_counts['test']['key1'] == 0
    
    # 添加重复的key
    key_manager.add_key('test', 'key1')
    assert len(key_manager._provider_keys['test']) == 1

def test_get_key_with_seed(key_manager):
    key_manager.add_key('test', 'key1')
    key_manager.add_key('test', 'key2')
    
    # 使用相同的seed应该得到相同的key
    key_manager.set_current_seed_once('seed1')
    key1 = key_manager.get_key('test')
    
    key_manager.set_current_seed_once('seed1')
    key2 = key_manager.get_key('test')
    
    assert key1 == key2
    assert key_manager._current_seed is None  # seed应该被清除

def test_get_key_load_balancing(key_manager):
    key_manager.add_key('test', 'key1')
    key_manager.add_key('test', 'key2')
    
    # 获取key多次，应该均匀分配
    keys = [key_manager.get_key('test') for _ in range(4)]
    counts = key_manager.get_key_counts('test')
    
    # 检查使用次数的差异不超过1
    count_values = list(counts.values())
    assert max(count_values) - min(count_values) <= 1

def test_clear_counts(key_manager):
    key_manager.add_key('test1', 'key1')
    key_manager.add_key('test2', 'key2')
    
    key_manager.get_key('test1')
    key_manager.get_key('test2')
    
    # 清除特定provider的计数
    key_manager.clear_counts('test1')
    assert key_manager._key_counts['test1']['key1'] == 0
    assert key_manager._key_counts['test2']['key2'] == 1
    
    # 清除所有计数
    key_manager.clear_counts()
    assert all(count == 0 for counts in key_manager._key_counts.values() 
              for count in counts.values())

def test_get_key_no_keys(key_manager):
    assert key_manager.get_key('nonexistent') is None

def test_get_key_counts(key_manager):
    key_manager.add_key('test', 'key1')
    key_manager.get_key('test')
    
    counts = key_manager.get_key_counts('test')
    assert counts['key1'] == 1
    
    # 测试获取不存在的provider的计数
    assert key_manager.get_key_counts('nonexistent') == {} 