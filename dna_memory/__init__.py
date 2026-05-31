"""
dna-memory — 多链 DNA 记忆匹配引擎

一个独立、轻量的记忆匹配核心库，基于多链 DNA 编码 + 加权投票 + 反链负反馈抑制。
源自在 Hermes Agent 中实战验证的神经蛊阵算法，抽离为独立包。

核心能力：
  1. 多链 DNA 编码 — 将查询文本映射到多个语义维度（域、意图、实体、模式等）
  2. 加权投票匹配 — 对候选实体库做多链加权评分
  3. 反链负反馈 — 每个实体的"不应该"特征词表，抑制假阳性
  4. 分歧驱动学习 — record_miss() 自动生成反链候选词
  5. 生命周期管理 — 反链按 origin 差异化半衰期衰减 (migration 14d / grown 30d)

无外部依赖，纯 Python 3.9+ 标准库。全部运算本地完成，零 token 消耗。
"""

__version__ = "0.1.0"

from .engine import DNAEncoder, DNAMatcher, MatchResult, AntiChain, record_miss
from .config import Config, demo_config, demo_entities

__all__ = [
    "DNAEncoder", "DNAMatcher", "MatchResult", "AntiChain", "record_miss",
    "Config", "demo_config", "demo_entities",
]
