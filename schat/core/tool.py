from dataclasses import dataclass
from typing import Dict, Any, Optional, List

@dataclass
class Tool:
    """工具调用"""
    name: str
    description: str
    parameters: Dict[str, Any]
    required: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "required": self.required
        } 