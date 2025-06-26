"""
Agent Mixins - Modular components for UniversalAgent
Prevents god-class anti-pattern by separating concerns
"""

from .base_mixin import BaseMixin
from .thinking_mixin import ThinkingMixin
from .tool_runner_mixin import ToolRunnerMixin
from .memory_mixin import MemoryMixin
from .llm_mixin import LLMMixin
from .communication_mixin import CommunicationMixin

__all__ = [
    'BaseMixin',
    'ThinkingMixin', 
    'ToolRunnerMixin',
    'MemoryMixin',
    'LLMMixin',
    'CommunicationMixin'
]