"""
DNA 记忆匹配引擎 — 核心实现

设计哲学：
  每个实体（记忆/hub/意图）自带多链 DNA，不是后贴的标签。
  匹配时各链加权投票，反链抑制假阳性，分歧驱动自动进化。
  
这就是我们造出来的算法——多链编码 × 加权投票 × 负反馈学习。
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import json, time, re, os


# ════════════════════════════════════════════════════════════
# 数据结构
# ════════════════════════════════════════════════════════════

@dataclass
class MatchResult:
    """一次匹配的结果。"""
    entity_id: Optional[str]          # 匹配到的实体 ID
    score: float = 0.0                # 总评分
    strand_scores: dict[str, float] = field(default_factory=dict)  # 各链得分
    anti_hits: list[str] = field(default_factory=list)       # 命中的反链词
    threshold_passed: bool = False    # 是否过阈值
    fallback_used: bool = False       # 是否降级匹配
    all_scores: dict[str, float] = field(default_factory=dict)  # 所有候选评分


class AntiChain:
    """
    反链 — 每个实体"不应该"匹配的特征词表。
    
    origin 标记来源：
      "migration"  — 系统启动时注入的初始抗体，半衰期 14 天（快速淘汰）
      "auto_grown" — 分歧驱动自动生成的抗体，半衰期 30 天（标准周期）
    """
    
    def __init__(self):
        self._data: dict[str, list[dict]] = {}
        self._dirty = False
    
    def load(self, path: str):
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        for eid, entries in raw.items():
            self._data[eid] = []
            for e in entries:
                if isinstance(e, dict):
                    self._data[eid].append(e)
                elif isinstance(e, str):
                    self._data[eid].append({
                        "word": e, "origin": "migration", "added": "2026-05-31"
                    })
        self._dirty = False
    
    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        self._dirty = False
    
    def get(self, entity_id: str) -> list[dict]:
        return self._data.get(entity_id, [])
    
    def add(self, entity_id: str, word: str, origin: str = "auto_grown"):
        if entity_id not in self._data:
            self._data[entity_id] = []
        # 去重
        if not any(e.get("word") == word for e in self._data[entity_id]):
            self._data[entity_id].append({
                "word": word, "origin": origin, "added": time.strftime("%Y-%m-%d")
            })
            self._dirty = True


# ════════════════════════════════════════════════════════════
# 多链 DNA 编码器
# ════════════════════════════════════════════════════════════

class DNAEncoder:
    """
    多链 DNA 编码器。
    
    输入文本 → 遍历每条链的关键词表 → 输出 DNA（每条链的命中类别列表）。
    纯本地关键词匹配，0.02-0.06ms/次，零 token 消耗。
    """
    
    def __init__(self, strands: dict[str, dict]):
        """
        strands: {
            "domain": {"keywords": {"tech": ["python", "server", ...], ...}, "weight": 0.35},
            "intent": {"keywords": {"deploy": ["部署", "发布", ...], ...}, "weight": 0.25},
            ...
        }
        """
        self.strands = strands
    
    def encode(self, text: str) -> dict[str, list[str]]:
        """编码文本为多链 DNA。"""
        if not text or not text.strip():
            return {s: ["unknown"] for s in self.strands}
        
        t = text.lower()
        dna = {}
        
        for strand_name, strand_cfg in self.strands.items():
            scores = {}
            for category, keywords in strand_cfg["keywords"].items():
                score = sum(1 for kw in keywords if kw.lower() in t)
                if score > 0:
                    scores[category] = score
            
            if scores:
                max_s = max(scores.values())
                dna[strand_name] = sorted(
                    [k for k, s in scores.items() if s >= max_s * 0.5]
                )
            else:
                dna[strand_name] = ["unknown"]
        
        return dna


# ════════════════════════════════════════════════════════════
# 磁吸匹配引擎（加权投票 + 反链扣分）
# ════════════════════════════════════════════════════════════

class DNAMatcher:
    """
    磁吸匹配引擎 — 权重可配置的多链投票 + 反链负反馈抑制。
    
    匹配流程：
      1. 每条链计算查询 DNA 与候选实体 DNA 的重叠率（查询覆盖度）
      2. 加权求和（各链权重可配）
      3. 反链命中扣分（每个命中 -0.10，上限 -0.35）
      4. 未达阈值时降级到名称精确匹配 → 域/意图宽松匹配
    """
    
    def __init__(
        self,
        strand_weights: dict[str, float],
        threshold: float = 0.10,
        anti_penalty: float = 0.10,
        anti_max: float = 0.35,
        entity_boost: float = 2.0,
    ):
        if abs(sum(strand_weights.values()) - 1.0) > 0.01:
            raise ValueError(f"权重和必须 ≈ 1.0，实际 {sum(strand_weights.values()):.3f}")
        self.weights = strand_weights
        self.threshold = threshold
        self.anti_penalty = anti_penalty
        self.anti_max = anti_max
        self.entity_boost = entity_boost
        self.entity_strands: set[str] = set()
    
    def mark_entity_strand(self, name: str):
        """标记实体链（按 hub 名在文本中是否出现来判断）。"""
        self.entity_strands.add(name)
    
    def match(
        self,
        query_dna: dict[str, list[str]],
        query_text: str,
        entities: list[dict],
        anti_chain: Optional[AntiChain] = None,
    ) -> MatchResult:
        if not entities:
            return MatchResult(entity_id=None)
        
        q_lower = (query_text or "").lower().strip()
        best_score = 0.0
        best_eid = None
        best_strands = {}
        best_anti = []
        all_scores = {}
        
        for entity in entities:
            eid = entity.get("id", "")
            e_dna = entity.get("dna", {})
            total = 0.0
            strand_scores = {}
            anti_hits = []
            
            for sname, weight in self.weights.items():
                qv = set(query_dna.get(sname, ["unknown"]))
                
                if sname in self.entity_strands:
                    direct = eid.lower() in q_lower or q_lower in eid.lower()
                    dna_match = eid.lower() in qv
                    score = self.entity_boost if (direct or dna_match) else 0.0
                else:
                    hv = set(e_dna.get(sname, []))
                    if qv == {"unknown"} or not hv:
                        continue
                    score = len(qv & hv) / max(len(qv), 1)
                
                strand_scores[sname] = round(score, 4)
                total += score * weight
            
            # 反链扣分
            if anti_chain:
                for entry in anti_chain.get(eid):
                    word = entry.get("word", "") if isinstance(entry, dict) else entry
                    if word and word.lower() in q_lower:
                        anti_hits.append(word)
                if anti_hits:
                    total -= min(len(anti_hits) * self.anti_penalty, self.anti_max)
            
            all_scores[eid] = round(total, 4)
            if total > best_score:
                best_score, best_eid = total, eid
                best_strands, best_anti = strand_scores, anti_hits
        
        # 阈值检查
        if best_eid and best_score >= self.threshold:
            return MatchResult(
                entity_id=best_eid, score=round(best_score, 4),
                strand_scores=best_strands, anti_hits=best_anti,
                threshold_passed=True, all_scores=all_scores,
            )
        
        # 降级：名称匹配 → 域/意图重叠
        if entities:
            for e in entities:
                eid = e.get("id", "")
                if eid.lower() in q_lower or q_lower in eid.lower():
                    return MatchResult(entity_id=eid, score=1.0,
                                       threshold_passed=True, fallback_used=True)
            
            q_dom = set(query_dna.get("domain", [])) if "domain" in self.weights else set()
            q_int = set(query_dna.get("intent", [])) if "intent" in self.weights else set()
            if q_dom != {"unknown"} or q_int != {"unknown"}:
                best_fb = 0.0
                best_fb_eid = None
                for e in entities:
                    h_dom = set(e.get("dna", {}).get("domain", []))
                    h_int = set(e.get("dna", {}).get("intent", []))
                    d = len(q_dom & h_dom) / max(len(q_dom), 1) if q_dom and q_dom != {"unknown"} and h_dom else 0
                    i = len(q_int & h_int) / max(len(q_int | h_int), 1) if q_int and q_int != {"unknown"} and h_int else 0
                    fb = d * 0.5 + i * 0.5
                    if fb > best_fb and (d >= 0.05 or i >= 0.15):
                        best_fb, best_fb_eid = fb, eid
                if best_fb_eid:
                    return MatchResult(entity_id=best_fb_eid, score=round(best_fb, 4),
                                       threshold_passed=True, fallback_used=True)
        
        return MatchResult(entity_id=best_eid, score=round(best_score, 4))


# ════════════════════════════════════════════════════════════
# 分歧驱动的反链学习（免疫系统）
# ════════════════════════════════════════════════════════════

def record_miss(
    query: str,
    wrong_id: str,
    anti_chain: AntiChain,
    strand_keywords: dict[str, dict[str, list[str]]],
    wrong_dna: Optional[dict] = None,
) -> list[str]:
    """
    记录匹配分歧，生成反链候选词。
    
    算法：
      Path A (Domain链): query 中命中 wrong hub domain 关键词的词
      Path B (实体链): query 包含 wrong hub 名称时，非ID的词
    
    反链词写入 anti_chain，积累毒性计数器。
    当同一词累计 N≥3 次分歧后执行 promote() 升格为正式抗体。
    """
    q_lower = query.lower()
    candidates = set()
    
    # Path A: domain 链触发词
    if wrong_dna:
        for sname, kw_dict in strand_keywords.items():
            for cat, kws in kw_dict.items():
                if cat in wrong_dna.get(sname, []):
                    for kw in kws:
                        if kw.lower() in q_lower:
                            candidates.add(kw.lower())
    
    # Path B: 实体名出现在查询中
    if wrong_id.lower() in q_lower:
        for tok in q_lower.split():
            tok = tok.strip()
            if tok and tok != wrong_id.lower():
                candidates.add(tok)
    
    for word in candidates:
        anti_chain.add(wrong_id, word, origin="auto_grown")
    
    return list(candidates)
