"""
Zep检索工具服务 (已迁移至 Neo4j)
封装图谱搜索、节点读取、边查询等工具，供 Report Agent 使用
"""

import time
import json
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient
from ..utils.neo4j_client import Neo4jClient

logger = get_logger('mirofish.zep_tools')


@dataclass
class SearchResult:
    """搜索结果"""
    facts: List[str]
    edges: List[Dict[str, Any]]
    nodes: List[Dict[str, Any]]
    query: str
    total_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "facts": self.facts,
            "edges": self.edges,
            "nodes": self.nodes,
            "query": self.query,
            "total_count": self.total_count
        }
    
    def to_text(self) -> str:
        """转换为文本格式，供LLM理解"""
        text_parts = [f"搜索查询: {self.query}", f"找到 {self.total_count} 条相关信息"]
        
        if self.facts:
            text_parts.append("\n### 相关事实:")
            for i, fact in enumerate(self.facts, 1):
                text_parts.append(f"{i}. {fact}")
        
        return "\n".join(text_parts)


@dataclass
class NodeInfo:
    """节点信息"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes
        }
    
    def to_text(self) -> str:
        """转换为文本格式"""
        entity_type = next((l for l in self.labels if l not in ["Entity", "Node"]), "未知类型")
        return f"实体: {self.name} (类型: {entity_type})\n摘要: {self.summary}"


@dataclass
class EdgeInfo:
    """边信息"""
    uuid: str
    name: str
    fact: str
    source_node_uuid: str
    target_node_uuid: str
    source_node_name: Optional[str] = None
    target_node_name: Optional[str] = None
    # 时间信息
    created_at: Optional[str] = None
    valid_at: Optional[str] = None
    invalid_at: Optional[str] = None
    expired_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "fact": self.fact,
            "source_node_uuid": self.source_node_uuid,
            "target_node_uuid": self.target_node_uuid,
            "source_node_name": self.source_node_name,
            "target_node_name": self.target_node_name,
            "created_at": self.created_at,
            "valid_at": self.valid_at,
            "invalid_at": self.invalid_at,
            "expired_at": self.expired_at
        }
    
    def to_text(self, include_temporal: bool = False) -> str:
        """转换为文本格式"""
        source = self.source_node_name or self.source_node_uuid[:8]
        target = self.target_node_name or self.target_node_uuid[:8]
        base_text = f"关系: {source} --[{self.name}]--> {target}\n事实: {self.fact}"
        
        if include_temporal:
            valid_at = self.valid_at or "未知"
            invalid_at = self.invalid_at or "至今"
            base_text += f"\n时效: {valid_at} - {invalid_at}"
            if self.expired_at:
                base_text += f" (已过期: {self.expired_at})"
        
        return base_text
    
    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        return self.expired_at is not None
    
    @property
    def is_invalid(self) -> bool:
        """是否已失效"""
        return self.invalid_at is not None


@dataclass
class InsightForgeResult:
    """
    深度洞察检索结果 (InsightForge)
    """
    query: str
    simulation_requirement: str
    sub_queries: List[str]
    semantic_facts: List[str] = field(default_factory=list)
    entity_insights: List[Dict[str, Any]] = field(default_factory=list)
    relationship_chains: List[str] = field(default_factory=list)
    total_facts: int = 0
    total_entities: int = 0
    total_relationships: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "simulation_requirement": self.simulation_requirement,
            "sub_queries": self.sub_queries,
            "semantic_facts": self.semantic_facts,
            "entity_insights": self.entity_insights,
            "relationship_chains": self.relationship_chains,
            "total_facts": self.total_facts,
            "total_entities": self.total_entities,
            "total_relationships": self.total_relationships
        }
    
    def to_text(self) -> str:
        """转换为详细的文本格式"""
        text_parts = [
            f"## 未来预测深度分析",
            f"分析问题: {self.query}",
            f"预测场景: {self.simulation_requirement}",
            f"\n### 预测数据统计",
            f"- 相关预测事实: {self.total_facts}条",
            f"- 涉及实体: {self.total_entities}个",
            f"- 关系链: {self.total_relationships}条"
        ]
        
        if self.sub_queries:
            text_parts.append(f"\n### 分析的子问题")
            for i, sq in enumerate(self.sub_queries, 1):
                text_parts.append(f"{i}. {sq}")
        
        if self.semantic_facts:
            text_parts.append(f"\n### 【关键事实】")
            for i, fact in enumerate(self.semantic_facts, 1):
                text_parts.append(f"{i}. \"{fact}\"")
        
        if self.entity_insights:
            text_parts.append(f"\n### 【核心实体】")
            for entity in self.entity_insights:
                text_parts.append(f"- **{entity.get('name', '未知')}** ({entity.get('type', '实体')})")
                if entity.get('summary'):
                    text_parts.append(f"  摘要: \"{entity.get('summary')}\"")
        
        return "\n".join(text_parts)


@dataclass
class PanoramaResult:
    """全貌搜索结果"""
    query: str
    active_facts: List[str] = field(default_factory=list)
    expired_facts: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0

    def to_text(self) -> str:
        text_parts = [f"## 全貌视图分析", f"查询: {self.query}"]
        if self.active_facts:
            text_parts.append("\n### 当前有效事实:")
            for i, f in enumerate(self.active_facts[:10], 1):
                text_parts.append(f"{i}. {f}")
        if self.expired_facts:
            text_parts.append("\n### 历史演变事实:")
            for i, f in enumerate(self.expired_facts[:10], 1):
                text_parts.append(f"{i}. {f}")
        return "\n".join(text_parts)


@dataclass
class InterviewResult:
    """采访结果"""
    topic: str
    interviews: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""

    def to_text(self) -> str:
        text_parts = [f"## Agent 深度采访实录", f"主题: {self.topic}", f"\n{self.summary}"]
        for item in self.interviews:
            text_parts.append(f"\n### 被采访者: {item.get('agent_name')} ({item.get('agent_role')})")
            text_parts.append(f"Q: {item.get('question')}")
            text_parts.append(f"A: {item.get('answer')}")
        return "\n".join(text_parts)


class ZepToolsService:
    """
    Neo4j 驱动的图谱检索工具服务
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.neo4j = Neo4jClient()
        self._llm_client = llm_client
        logger.info("ZepToolsService (Neo4j) 初始化完成")
    
    @property
    def llm(self) -> LLMClient:
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client
    
    def search_graph(
        self, 
        graph_id: str, 
        query: str, 
        limit: int = 10,
        scope: str = "edges"
    ) -> SearchResult:
        """
        图谱搜索（目前在 Neo4j 中使用关键词匹配模拟，未来可加入向量搜索）
        """
        logger.info(f"图谱搜索 (Neo4j): graph_id={graph_id}, query={query[:50]}...")
        
        # 降级：使用本地关键词匹配搜索
        return self._local_search(graph_id, query, limit, scope)
    
    def _local_search(
        self, 
        graph_id: str, 
        query: str, 
        limit: int = 10,
        scope: str = "edges"
    ) -> SearchResult:
        """
        本地搜索实现
        """
        facts = []
        edges_result = []
        nodes_result = []
        
        # 简单关键词提取
        keywords = [w.strip() for w in query.lower().split() if len(w.strip()) > 1]
        
        if scope in ["edges", "both"]:
            # 获取所有边并过滤
            all_edges = self.get_all_edges(graph_id)
            for edge in all_edges:
                text = f"{edge.fact} {edge.name}".lower()
                if any(k in text for k in keywords) or query.lower() in text:
                    edges_result.append(edge.to_dict())
                    facts.append(edge.fact)
            
        if scope in ["nodes", "both"]:
            # 获取所有节点并过滤
            all_nodes = self.get_all_nodes(graph_id)
            for node in all_nodes:
                text = f"{node.name} {node.summary}".lower()
                if any(k in text for k in keywords) or query.lower() in text:
                    nodes_result.append(node.to_dict())
                    facts.append(f"[{node.name}]: {node.summary}")
                    
        # 限制数量
        facts = list(set(facts))[:limit]
        
        return SearchResult(
            facts=facts,
            edges=edges_result[:limit],
            nodes=nodes_result[:limit],
            query=query,
            total_count=len(facts)
        )

    def get_all_nodes(self, graph_id: str) -> List[NodeInfo]:
        """获取所有节点"""
        # 使用 properties(n)
        query = "MATCH (n {graph_id: $graph_id}) RETURN properties(n) as n_props, labels(n) as labels"
        results = self.neo4j.execute_read(query, {"graph_id": graph_id})
        
        nodes = []
        for row in results:
            n = row["n_props"]
            nodes.append(NodeInfo(
                uuid=n.get("uuid", ""),
                name=n.get("name", ""),
                labels=row["labels"],
                summary=n.get("summary", ""),
                attributes={k: v for k, v in n.items() if k not in ["uuid", "name", "summary", "graph_id"]}
            ))
        return nodes

    def get_all_edges(self, graph_id: str) -> List[EdgeInfo]:
        """获取所有边"""
        # 使用 properties(r)
        query = """
        MATCH (a {graph_id: $graph_id})-[r]->(b {graph_id: $graph_id}) 
        RETURN properties(r) as r_props, type(r) as type, a.uuid as s_uuid, b.uuid as t_uuid, a.name as s_name, b.name as t_name
        """
        results = self.neo4j.execute_read(query, {"graph_id": graph_id})
        
        edges = []
        for row in results:
            r = row["r_props"]
            edges.append(EdgeInfo(
                uuid=r.get("uuid", ""),
                name=row["type"],
                fact=r.get("fact", f"{row['s_name']} {row['type']} {row['t_name']}"),
                source_node_uuid=row["s_uuid"],
                target_node_uuid=row["t_uuid"],
                source_node_name=row["s_name"],
                target_node_name=row["t_name"]
            ))
        return edges

    def get_node_detail(self, graph_id: str, node_uuid: str) -> Optional[NodeInfo]:
        """获取节点详情"""
        # 使用 properties(n)
        query = "MATCH (n {graph_id: $graph_id, uuid: $uuid}) RETURN properties(n) as n_props, labels(n) as labels"
        results = self.neo4j.execute_read(query, {"graph_id": graph_id, "uuid": node_uuid})
        
        if not results:
            return None
            
        row = results[0]
        n = row["n_props"]
        return NodeInfo(
            uuid=n.get("uuid", ""),
            name=n.get("name", ""),
            labels=row["labels"],
            summary=n.get("summary", ""),
            attributes={k: v for k, v in n.items() if k not in ["uuid", "name", "summary", "graph_id"]}
        )

    def get_node_edges(self, graph_id: str, node_uuid: str) -> List[EdgeInfo]:
        """获取节点相关的边"""
        # 使用 properties(r)
        query = """
        MATCH (a {graph_id: $graph_id, uuid: $uuid})-[r]-(b {graph_id: $graph_id}) 
        RETURN properties(r) as r_props, type(r) as type, a.uuid as s_uuid, b.uuid as t_uuid, a.name as s_name, b.name as t_name
        """
        results = self.neo4j.execute_read(query, {"graph_id": graph_id, "uuid": node_uuid})
        
        edges = []
        for row in results:
            r = row["r_props"]
            edges.append(EdgeInfo(
                uuid=r.get("uuid", ""),
                name=row["type"],
                fact=r.get("fact", f"{row['s_name']} {row['type']} {row['t_name']}"),
                source_node_uuid=row["s_uuid"],
                target_node_uuid=row["t_uuid"],
                source_node_name=row["s_name"],
                target_node_name=row["t_name"]
            ))
        return edges

    def get_simulation_context(self, graph_id: str, simulation_requirement: str) -> Dict[str, Any]:
        """
        获取模拟上下文，用于报告规划
        """
        logger.info(f"获取模拟上下文: graph_id={graph_id}")
        
        # 1. 获取图谱统计信息
        stats = self.get_graph_statistics(graph_id)
        
        # 2. 转换键名以匹配 ReportAgent 的期望
        graph_stats = {
            "total_nodes": stats.get("node_count", 0),
            "total_edges": stats.get("edge_count", 0),
            "entity_types": {label: 0 for label in stats.get("labels", [])}  # 简化处理，仅提供类型列表
        }
        
        # 3. 获取相关预测事实样本
        search_res = self.search_graph(graph_id, simulation_requirement, limit=20)
        
        return {
            "graph_statistics": graph_stats,
            "total_entities": stats.get("node_count", 0),
            "related_facts": search_res.facts,
            "simulation_requirement": simulation_requirement
        }

    def insight_forge(self, graph_id: str, query: str, simulation_requirement: str, report_context: str = "") -> InsightForgeResult:
        """
        深度洞察检索实现
        """
        # 1. 生成子问题
        prompt = f"针对以下分析问题和场景，生成3-5个子问题以进行多维度检索：\n问题：{query}\n场景：{simulation_requirement}\n上下文：{report_context}"
        # 简单实现，实际应调用 LLM
        sub_queries = [query] 
        
        # 2. 检索各维度
        search_res = self.search_graph(graph_id, query, limit=20)
        
        return InsightForgeResult(
            query=query,
            simulation_requirement=simulation_requirement,
            sub_queries=sub_queries,
            semantic_facts=search_res.facts,
            total_facts=len(search_res.facts),
            total_entities=len(search_res.nodes),
            total_relationships=len(search_res.edges)
        )

    def panorama_search(self, graph_id: str, query: str, include_expired: bool = True) -> PanoramaResult:
        """广度全貌搜索"""
        search_res = self.search_graph(graph_id, query, limit=30)
        return PanoramaResult(
            query=query,
            active_facts=search_res.facts,
            total_count=len(search_res.facts)
        )

    def quick_search(self, graph_id: str, query: str, limit: int = 10) -> str:
        """快速检索，返回文本"""
        search_res = self.search_graph(graph_id, query, limit=limit)
        return search_res.to_text()

    def interview_agents(self, simulation_id: str, interview_requirement: str, simulation_requirement: str, max_agents: int = 5) -> InterviewResult:
        """采访模拟 Agent (模拟实现)"""
        # 在本地 Neo4j 版本中，我们模拟采访结果
        return InterviewResult(
            topic=interview_requirement,
            summary=f"针对场景 '{simulation_requirement}' 的采访摘要。",
            interviews=[
                {
                    "agent_name": "模拟角色A",
                    "agent_role": "学生",
                    "question": f"关于{interview_requirement}，你怎么看？",
                    "answer": "这是一个非常值得关注的问题，我认为我们需要更多的透明度。"
                }
            ]
        )

    def get_graph_statistics(self, graph_id: str) -> Dict[str, Any]:
        """获取图谱统计信息"""
        nodes = self.get_all_nodes(graph_id)
        edges = self.get_all_edges(graph_id)
        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "labels": list(set([label for n in nodes for label in n.labels]))
        }

    def get_entity_summary(self, graph_id: str, entity_name: str) -> Dict[str, Any]:
        """获取实体摘要"""
        # 使用 properties(n)
        query = "MATCH (n {graph_id: $graph_id}) WHERE n.name = $name RETURN properties(n) as n_props"
        results = self.neo4j.execute_read(query, {"graph_id": graph_id, "name": entity_name})
        if results:
            return results[0]["n_props"]
        return {}

    def get_entities_by_type(self, graph_id: str, entity_type: str) -> List[NodeInfo]:
        """按类型获取实体"""
        # 使用 properties(n)
        query = f"MATCH (n:{entity_type} {{graph_id: $graph_id}}) RETURN properties(n) as n_props, labels(n) as labels"
        results = self.neo4j.execute_read(query, {"graph_id": graph_id})
        nodes = []
        for row in results:
            n = row["n_props"]
            nodes.append(NodeInfo(
                uuid=n.get("uuid", ""),
                name=n.get("name", ""),
                labels=row["labels"],
                summary=n.get("summary", ""),
                attributes={k: v for k, v in n.items() if k not in ["uuid", "name", "summary", "graph_id"]}
            ))
        return nodes
