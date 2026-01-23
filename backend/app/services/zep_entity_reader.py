"""
Zep实体读取与过滤服务
已改造为使用本地 Neo4j
"""

import time
from typing import Dict, Any, List, Optional, Set, Callable, TypeVar
from dataclasses import dataclass, field

from ..config import Config
from ..utils.logger import get_logger
from ..utils.neo4j_client import Neo4jClient

logger = get_logger('mirofish.zep_entity_reader')

# 用于泛型返回类型
T = TypeVar('T')


@dataclass
class EntityNode:
    """实体节点数据结构"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    # 相关的边信息
    related_edges: List[Dict[str, Any]] = field(default_factory=list)
    # 相关的其他节点信息
    related_nodes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes,
            "related_edges": self.related_edges,
            "related_nodes": self.related_nodes,
        }
    
    def get_entity_type(self) -> Optional[str]:
        """获取实体类型（排除默认的Entity标签）"""
        for label in self.labels:
            if label not in ["Entity", "Node"]:
                return label
        return None


@dataclass
class FilteredEntities:
    """过滤后的实体集合"""
    entities: List[EntityNode]
    entity_types: Set[str]
    total_count: int
    filtered_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "entity_types": list(self.entity_types),
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
        }


class ZepEntityReader:
    """
    实体读取与过滤服务 (Neo4j 版本)
    
    主要功能：
    1. 从 Neo4j 图谱读取所有节点
    2. 筛选出符合预定义实体类型的节点
    3. 获取每个实体的相关边和关联节点信息
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # 兼容旧接口，api_key 参数不再使用
        self.neo4j = Neo4jClient()
    
    def get_all_nodes(self, graph_id: str) -> List[Dict[str, Any]]:
        """获取图谱的所有节点"""
        logger.info(f"获取图谱 {graph_id} 的所有节点...")
        
        # 使用 properties(n) 确保返回字典
        query = "MATCH (n {graph_id: $graph_id}) RETURN properties(n) as n_props, labels(n) as labels"
        results = self.neo4j.execute_read(query, {"graph_id": graph_id})
        
        nodes_data = []
        for row in results:
            node = row["n_props"]
            labels = row["labels"]
            nodes_data.append({
                "uuid": node.get("uuid", ""),
                "name": node.get("name", ""),
                "labels": labels,
                "summary": node.get("summary", ""),
                "attributes": {k: v for k, v in node.items() if k not in ["uuid", "name", "summary", "graph_id", "created_at", "updated_at"]},
            })
        
        logger.info(f"共获取 {len(nodes_data)} 个节点")
        return nodes_data
    
    def get_all_edges(self, graph_id: str) -> List[Dict[str, Any]]:
        """获取图谱的所有边"""
        logger.info(f"获取图谱 {graph_id} 的所有边...")
        
        # 使用 properties(r)
        query = """
        MATCH (a {graph_id: $graph_id})-[r]->(b {graph_id: $graph_id})
        RETURN properties(r) as r_props, type(r) as type, a.uuid as source_uuid, b.uuid as target_uuid, a.name as source_name, b.name as target_name
        """
        results = self.neo4j.execute_read(query, {"graph_id": graph_id})
        
        edges_data = []
        for row in results:
            edge = row["r_props"]
            edges_data.append({
                "uuid": edge.get("uuid", ""),
                "name": row["type"],
                "fact": f"{row['source_name']} {row['type']} {row['target_name']}",
                "source_node_uuid": row["source_uuid"],
                "target_node_uuid": row["target_uuid"],
                "attributes": {k: v for k, v in edge.items() if k not in ["uuid", "graph_id", "created_at", "updated_at"]},
            })
        
        logger.info(f"共获取 {len(edges_data)} 条边")
        return edges_data
    
    def get_node_edges(self, node_uuid: str) -> List[Dict[str, Any]]:
        """获取指定节点的所有相关边"""
        # 使用 properties(r) 和 properties(startNode(r))
        query = """
        MATCH (a {uuid: $uuid})-[r]-(b)
        RETURN properties(r) as r_props, type(r) as type, a.uuid as a_uuid, b.uuid as b_uuid, properties(startNode(r)) as start_node_props
        """
        results = self.neo4j.execute_read(query, {"uuid": node_uuid})
        
        edges_data = []
        for row in results:
            edge = row["r_props"]
            start_node = row["start_node_props"]
            # 确定方向
            # 简化逻辑：我们直接取 startNode 的 uuid 作为 source
            source_node_uuid = start_node.get("uuid")
            target_node_uuid = row["b_uuid"] if row["a_uuid"] == source_node_uuid else row["a_uuid"]
            
            edges_data.append({
                "uuid": edge.get("uuid", ""),
                "name": row["type"],
                "fact": "", # 简化
                "source_node_uuid": source_node_uuid,
                "target_node_uuid": target_node_uuid,
                "attributes": {k: v for k, v in edge.items() if k not in ["uuid", "graph_id", "created_at", "updated_at"]},
            })
            
        return edges_data
    
    def filter_defined_entities(
        self, 
        graph_id: str,
        defined_entity_types: Optional[List[str]] = None,
        enrich_with_edges: bool = True
    ) -> FilteredEntities:
        """筛选出符合预定义实体类型的节点"""
        logger.info(f"开始筛选图谱 {graph_id} 的实体...")
        
        # 获取所有节点
        all_nodes = self.get_all_nodes(graph_id)
        total_count = len(all_nodes)
        
        # 筛选符合条件的实体
        filtered_entities = []
        entity_types_found = set()
        
        for node in all_nodes:
            labels = node.get("labels", [])
            custom_labels = [l for l in labels if l not in ["Entity", "Node"]]
            
            if not custom_labels:
                continue
            
            if defined_entity_types:
                matching_labels = [l for l in custom_labels if l in defined_entity_types]
                if not matching_labels:
                    continue
                entity_type = matching_labels[0]
            else:
                entity_type = custom_labels[0]
            
            entity_types_found.add(entity_type)
            
            entity = EntityNode(
                uuid=node["uuid"],
                name=node["name"],
                labels=labels,
                summary=node["summary"],
                attributes=node["attributes"],
            )
            
            if enrich_with_edges:
                # 使用 Cypher 高效查询相关边
                edges = self.get_node_edges(node["uuid"])
                related_edges = []
                related_node_uuids = set()
                
                for edge in edges:
                    if edge["source_node_uuid"] == node["uuid"]:
                        related_edges.append({
                            "direction": "outgoing",
                            "edge_name": edge["name"],
                            "fact": "",
                            "target_node_uuid": edge["target_node_uuid"],
                        })
                        related_node_uuids.add(edge["target_node_uuid"])
                    else:
                        related_edges.append({
                            "direction": "incoming",
                            "edge_name": edge["name"],
                            "fact": "",
                            "source_node_uuid": edge["source_node_uuid"],
                        })
                        related_node_uuids.add(edge["source_node_uuid"])
                
                entity.related_edges = related_edges
                
                # 批量获取关联节点信息
                if related_node_uuids:
                    q_nodes = "MATCH (n) WHERE n.uuid IN $uuids RETURN properties(n) as n_props, labels(n) as labels"
                    res_nodes = self.neo4j.execute_read(q_nodes, {"uuids": list(related_node_uuids)})
                    
                    related_nodes_info = []
                    for r in res_nodes:
                        rn = r["n_props"]
                        related_nodes_info.append({
                            "uuid": rn.get("uuid"),
                            "name": rn.get("name"),
                            "labels": r["labels"],
                            "summary": rn.get("summary", ""),
                        })
                    entity.related_nodes = related_nodes_info
            
            filtered_entities.append(entity)
        
        return FilteredEntities(
            entities=filtered_entities,
            entity_types=entity_types_found,
            total_count=total_count,
            filtered_count=len(filtered_entities),
        )
    
    def get_entity_with_context(
        self, 
        graph_id: str, 
        entity_uuid: str
    ) -> Optional[EntityNode]:
        """获取单个实体及其完整上下文"""
        query = "MATCH (n {uuid: $uuid}) RETURN properties(n) as n_props, labels(n) as labels"
        results = self.neo4j.execute_read(query, {"uuid": entity_uuid})
        
        if not results:
            return None
            
        node = results[0]["n_props"]
        labels = results[0]["labels"]
        
        entity = EntityNode(
            uuid=node.get("uuid", ""),
            name=node.get("name", ""),
            labels=labels,
            summary=node.get("summary", ""),
            attributes={k: v for k, v in node.items() if k not in ["uuid", "name", "summary", "graph_id", "created_at", "updated_at"]},
        )
        
        # 获取上下文（复用逻辑）
        # 这里为了简单，直接调用 filter_defined_entities 的内部逻辑的简化版
        # 但为了保持代码整洁，我们重新实现一次边查询
        
        edges = self.get_node_edges(entity_uuid)
        related_edges = []
        related_node_uuids = set()
        
        for edge in edges:
            if edge["source_node_uuid"] == entity_uuid:
                related_edges.append({
                    "direction": "outgoing",
                    "edge_name": edge["name"],
                    "fact": "",
                    "target_node_uuid": edge["target_node_uuid"],
                })
                related_node_uuids.add(edge["target_node_uuid"])
            else:
                related_edges.append({
                    "direction": "incoming",
                    "edge_name": edge["name"],
                    "fact": "",
                    "source_node_uuid": edge["source_node_uuid"],
                })
                related_node_uuids.add(edge["source_node_uuid"])
        
        entity.related_edges = related_edges
        
        if related_node_uuids:
            q_nodes = "MATCH (n) WHERE n.uuid IN $uuids RETURN properties(n) as n_props, labels(n) as labels"
            res_nodes = self.neo4j.execute_read(q_nodes, {"uuids": list(related_node_uuids)})
            
            related_nodes_info = []
            for r in res_nodes:
                rn = r["n_props"]
                related_nodes_info.append({
                    "uuid": rn.get("uuid"),
                    "name": rn.get("name"),
                    "labels": r["labels"],
                    "summary": rn.get("summary", ""),
                })
            entity.related_nodes = related_nodes_info
            
        return entity
    
    def get_entities_by_type(
        self, 
        graph_id: str, 
        entity_type: str,
        enrich_with_edges: bool = True
    ) -> List[EntityNode]:
        """获取指定类型的所有实体"""
        result = self.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=[entity_type],
            enrich_with_edges=enrich_with_edges
        )
        return result.entities
