"""
游戏公司岗位测试自动化模块
"""

from .automators import (
    BaseAutomator,
    TestContext,
    AutomatorFactory,
    run_automated_test,
    # 具体实现
    VisualStudioAutomator,
    UnrealEngineAutomator,
    MayaAutomator,
    BlenderAutomator,
    PhotoshopAutomator,
    PremiereProAutomator,
    AfterEffectsAutomator,
)

__all__ = [
    'BaseAutomator',
    'TestContext', 
    'AutomatorFactory',
    'run_automated_test',
    'VisualStudioAutomator',
    'UnrealEngineAutomator',
    'MayaAutomator',
    'BlenderAutomator',
    'PhotoshopAutomator',
    'PremiereProAutomator',
    'AfterEffectsAutomator',
]
