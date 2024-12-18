import pytest
from schat.models.factory import ModelFactory
from schat.models.base import Model
from schat.models.openai import OpenAIModel
from tests.conftest import MockModel

def test_get_model_basic():
    """测试基本的模型获取"""
    model = ModelFactory.get_model("openai")
    assert isinstance(model, OpenAIModel)
    assert model.provider == "openai"

def test_get_model_with_model_name():
    """测试带模型名称的获取"""
    model = ModelFactory.get_model("openai:gpt-4")
    assert isinstance(model, OpenAIModel)
    assert model.get_model_config()["model"] == "gpt-4"

def test_get_model_singleton():
    """测试模型实例的单例性"""
    model1 = ModelFactory.get_model("openai:gpt-4")
    model2 = ModelFactory.get_model("openai:gpt-4")
    assert model1 is model2

def test_register_provider():
    """测试注册新的provider"""
    # 注册一个新的provider
    ModelFactory.register_provider(
        "custom",
        model_class=MockModel,
        base_url="https://api.custom.com",
        default_params={"model": "custom-model"}
    )
    
    # 获取注册的模型
    model = ModelFactory.get_model("custom")
    assert isinstance(model, MockModel)
    assert model.provider == "custom"
    assert model.base_url == "https://api.custom.com"
    assert model.get_model_config()["model"] == "custom-model"

def test_get_model_with_config():
    """测试获取模型时传入配置"""
    model = ModelFactory.get_model("openai", temperature=0.8, model="gpt-4")
    assert model.get_model_config()["temperature"] == 0.8
    assert model.get_model_config()["model"] == "gpt-4"

def test_set_model_config():
    """测试设置模型配置"""
    model = ModelFactory.get_model("openai")
    ModelFactory.set_model_config("openai", {"temperature": 0.9})
    assert model.get_model_config()["temperature"] == 0.9

def test_get_model_unknown_provider():
    """测试获取未知provider的模型"""
    with pytest.raises(ValueError, match="Unknown provider"):
        ModelFactory.get_model("unknown")

def test_openai_compatible_provider():
    """测试OpenAI兼容的provider"""
    ModelFactory.register_provider(
        "compatible",
        base_url="https://api.compatible.com",
        openai_compatible=True,
        default_params={"model": "compatible-model"}
    )
    
    model = ModelFactory.get_model("compatible")
    assert isinstance(model, OpenAIModel)
    assert model.base_url == "https://api.compatible.com"