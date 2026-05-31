# DNA Memory — 多链 DNA 记忆匹配引擎

**零依赖 · 零 Token · 亚毫秒级匹配**

```python
pip install dna-memory
```

这是一个基于**多链 DNA 编码 + 加权投票 + 反链负反馈抑制**的记忆匹配引擎。
源自在 Hermes Agent 中实战验证的[神经蛊阵算法](https://github.com/asdfdsa1ceacse/neural-gu-zhen)，抽离为独立包。

---

## 为什么需要它？

现有的记忆检索方案（Mem0、Hindsight 等）都需要 Agent **显式 API 调用**才能存取记忆。
Agent 必须"知道自己需要记忆"——但这恰恰是最难的问题。

DNA Memory 的核心思想：**每个实体自带多链 DNA，不是后贴的标签。匹配时各链加权投票，反链抑制假阳性，分歧驱动自动进化。**

- **自动注入** — 无需 Agent 主动调用，消息经过时自动匹配
- **零 Token** — 全部本地关键词匹配，0.02-0.06ms/次
- **反链免疫** — 错误匹配自动产生抗体，下次不再犯
- **可解释** — 每步可追踪（DNA→投票→反链→结果）

## 快速开始

```python
from dna_memory import Config, DNAEncoder, DNAMatcher, AntiChain

# 1. 配置 5 条链
config = Config()
config.add_strand("domain", {
    "tech": ["python", "docker", "server", "技术", "服务器", "系统"],
    "video": ["视频", "生成", "渲染", "动画", "工作流"],
    "memory": ["记忆", "hindsight", "recall", "虫洞", "生态", "框架"],
}, weight=0.30)
config.add_strand("intent", {
    "deploy": ["部署", "安装", "启动"],
    "fix": ["修复", "修改", "更新"],
    "query": ["查询", "查看", "检查"],
}, weight=0.20)

# 2. 编码器 + 匹配器
encoder = DNAEncoder(config.strands)
matcher = DNAMatcher(config.weights())
matcher.mark_entity_strand("entity")  # 标记实体链

# 3. 实体库
entities = [
    {"id": "devops", "dna": {"domain": ["tech"], "intent": ["deploy", "fix"]}},
    {"id": "video_tool", "dna": {"domain": ["video"], "intent": ["build"]}},
    {"id": "memory_sys", "dna": {"domain": ["memory"], "intent": ["query"]}},
]

# 4. 匹配
dna = encoder.encode("帮我修复服务器部署")
result = matcher.match(dna, "帮我修复服务器部署", entities)
print(result.entity_id)  # → "devops"
print(result.score)      # → 0.50
```

## 反链免疫系统

```python
from dna_memory import AntiChain, record_miss

anti = AntiChain()

# 错误匹配后自动学习
record_miss(
    query="帮我部署视频工作流",
    wrong_id="memory_sys",  # 匹配错了
    anti_chain=anti,
    strand_keywords=config.strands,
    wrong_dna={"domain": ["memory"], "intent": ["query"]},
)

# "视频" 和 "工作流" 被加入 memory_sys 的反链
# 下次 "视频工作流" 不会错误匹配到 memory_sys

anti.save("my_antibodies.json")
```

## 基准性能

| 操作 | 耗时 |
|------|:----:|
| DNA 五链编码 | **0.02-0.06ms** |
| 磁吸匹配（10 实体） | **0.08ms** |
| 反链扣分 | **0.01ms** |
| 全链路 | **< 0.2ms** |
| Token 消耗 | **0** |

## 设计文档

完整算法设计见：[神经蛊阵论文 v3](https://github.com/asdfdsa1ceacse/neural-gu-zhen)

## 许可证

MIT License — 自由使用、修改、商用。
