"""
配置模块 — 链定义 + 演示数据
"""

from .engine import DNAEncoder


class Config:
    """多链 DNA 配置。"""
    
    def __init__(self):
        self.strands: dict[str, dict] = {}
    
    def add_strand(self, name: str, keywords: dict[str, list[str]],
                   weight: float = 0.20, is_entity: bool = False):
        """添加一条链。"""
        self.strands[name] = {
            "keywords": {k: [str(w).lower() for w in v] for k, v in keywords.items()},
            "weight": round(weight, 4),
            "is_entity": is_entity,
        }
        return self
    
    def weights(self) -> dict[str, float]:
        return {s: c["weight"] for s, c in self.strands.items()}
    
    def entity_strands(self) -> list[str]:
        return [s for s, c in self.strands.items() if c.get("is_entity")]


def demo_config() -> Config:
    """默认演示配置（适合中文记忆场景）。"""
    cfg = Config()
    cfg.add_strand("domain", {
        "tech": ["python", "docker", "api", "server", "deploy", "技术", "服务器", "系统"],
        "video": ["视频", "生成", "渲染", "动画", "工作流", "comfyui", "wan"],
        "memory": ["记忆", "hindsight", "recall", "虫洞", "wormhole", "生态", "框架"],
        "arch": ["配置", "安装", "部署", "系统", "架构", "环境"],
        "gpu": ["gpu", "显卡", "显存", "服务器", "端脑", "算力"],
    }, weight=0.30)
    cfg.add_strand("intent", {
        "deploy": ["部署", "安装", "启动", "搭建"],
        "fix": ["修复", "修改", "更新", "清理"],
        "query": ["查询", "查看", "检查", "搜索"],
        "learn": ["学习", "怎么", "如何", "教程"],
        "build": ["构建", "创建", "编写", "生成"],
    }, weight=0.20)
    cfg.add_strand("entity", {
        "hermes": ["hermes", "代理人"],
        "comfyui": ["comfyui", "comfy"],
        "hindsight": ["hindsight"],
        "sdxl": ["sdxl", "sd"],
        "wan2.2": ["wan2.2", "wan"],
    }, weight=0.25, is_entity=True)
    cfg.add_strand("pattern", {
        "tutorial": ["教程", "指南", "怎么", "步骤"],
        "config": ["配置", "设置", "参数", "选项"],
        "workflow": ["工作流", "流程", "管线"],
        "troubleshoot": ["问题", "报错", "错误", "异常"],
    }, weight=0.15)
    cfg.add_strand("context", {
        "question": ["吗", "怎么", "什么", "如何", "为什么"],
        "request": ["帮我", "我要", "给我", "做"],
    }, weight=0.10)
    return cfg


def demo_entities() -> list[dict]:
    """默认演示实体库（8 个 hub）。"""
    return [
        {"id": "comfyui", "dna": {"domain": ["video", "gpu"], "intent": ["deploy", "build", "learn"],
                                   "pattern": ["workflow", "tutorial"]}},
        {"id": "hermes", "dna": {"domain": ["arch", "tool"], "intent": ["deploy", "fix", "query"],
                                  "pattern": ["config", "tutorial"]}},
        {"id": "hindsight", "dna": {"domain": ["memory"], "intent": ["query", "fix"],
                                     "pattern": ["troubleshoot"]}},
        {"id": "sdxl", "dna": {"domain": ["video"], "intent": ["deploy", "build"],
                                "pattern": ["workflow", "tutorial"]}},
        {"id": "wan2.2", "dna": {"domain": ["video"], "intent": ["deploy", "build"],
                                  "pattern": ["workflow", "tutorial"]}},
        {"id": "端脑云", "dna": {"domain": ["gpu"], "intent": ["deploy", "build"],
                                 "pattern": ["workflow"]}},
    ]
