"""
图谱构建服务
使用本地 Neo4j 和 LLM 提取构建图谱
"""

import os
import uuid
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from ..config import Config
from ..models.task import TaskManager, TaskStatus
from .text_processor import TextProcessor
from ..utils.neo4j_client import Neo4jClient
from .graph_extractor import GraphExtractor
from ..utils.logger import get_logger

logger = get_logger('mirofish.services.graph_builder')

@dataclass
class GraphInfo:
    """图谱信息"""
    graph_id: str
    node_count: int
    edge_count: int
    entity_types: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "entity_types": self.entity_types,
        }

class GraphBuilderService:
    """
    图谱构建服务
    负责调用 GraphExtractor 提取实体并写入 Neo4j
    """
    
    def __init__(self):
        self.neo4j = Neo4jClient()
        self.extractor = GraphExtractor()
        self.task_manager = TaskManager()
    
    def build_graph_async(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "MiroFish Graph",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 3
    ) -> str:
        """异步构建图谱"""
        task_id = self.task_manager.create_task(
            task_type="graph_build",
            metadata={
                "graph_name": graph_name,
                "chunk_size": chunk_size,
                "text_length": len(text),
            }
        )
        
        thread = threading.Thread(
            target=self._build_graph_worker,
            args=(task_id, text, ontology, graph_name, chunk_size, chunk_overlap, batch_size)
        )
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _build_graph_worker(
        self,
        task_id: str,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        batch_size: int
    ):
        """图谱构建工作线程"""
        try:
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                progress=5,
                message="开始构建图谱..."
            )
            
            # 1. 创建图谱标识
            graph_id = f"mirofish_{uuid.uuid4().hex[:16]}"
            self.task_manager.update_task(
                task_id,
                progress=10,
                message=f"图谱标识已创建: {graph_id}"
            )
            
            # 2. 文本分块
            chunks = TextProcessor.split_text(text, chunk_size, chunk_overlap)
            total_chunks = len(chunks)
            self.task_manager.update_task(
                task_id,
                progress=20,
                message=f"文本已分割为 {total_chunks} 个块"
            )
            
            # 3. 提取并写入 Neo4j
            for i, chunk in enumerate(chunks):
                progress = 20 + int((i + 1) / total_chunks * 70)
                self.task_manager.update_task(
                    task_id,
                    progress=progress,
                    message=f"正在处理第 {i+1}/{total_chunks} 个文本块..."
                )
                
                # 提取
                extracted_data = self.extractor.extract(chunk)
                
                # 写入 Neo4j
                self._write_to_neo4j(graph_id, extracted_data)
                
                # 避免过快
                time.sleep(0.5)
            
            # 4. 获取图谱信息
            self.task_manager.update_task(
                task_id,
                progress=95,
                message="获取图谱信息..."
            )
            
            graph_info = self._get_graph_info(graph_id)
            
            # 完成
            self.task_manager.complete_task(task_id, {
                "graph_id": graph_id,
                "graph_info": graph_info.to_dict(),
                "chunks_processed": total_chunks,
            })
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"Graph build failed: {error_msg}")
            self.task_manager.fail_task(task_id, error_msg)
    
    def _write_to_neo4j(self, graph_id: str, data: Dict[str, Any]):
        """将提取的数据写入 Neo4j"""
        # 写入节点
        for node in data.get("nodes", []):
            name = node.get("name")
            label = node.get("label", "Entity")
            summary = node.get("summary", "")
            props = node.get("properties", {})
            
            # 使用 MERGE 确保节点唯一性（在同一图谱内）
            query = (
                f"MERGE (n:`{label}` {{name: $name, graph_id: $graph_id}}) "
                f"ON CREATE SET n.uuid = $uuid, n.created_at = datetime() "
                f"SET n += $props, n.summary = $summary, n.updated_at = datetime()"
            )
            self.neo4j.execute_query(query, {
                "name": name,
                "graph_id": graph_id,
                "uuid": uuid.uuid4().hex,
                "props": props,
                "summary": summary
            })
            
        # 写入关系
        for edge in data.get("edges", []):
            source_name = edge.get("from")
            target_name = edge.get("to")
            rel_type = edge.get("relationship", "RELATED_TO").replace(" ", "_").upper()
            props = edge.get("properties", {})
            
            query = (
                f"MATCH (a {{name: $source_name, graph_id: $graph_id}}) "
                f"MATCH (b {{name: $target_name, graph_id: $graph_id}}) "
                f"MERGE (a)-[r:`{rel_type}`]->(b) "
                f"ON CREATE SET r.uuid = $uuid, r.created_at = datetime() "
                f"SET r += $props, r.updated_at = datetime()"
            )
            self.neo4j.execute_query(query, {
                "source_name": source_name,
                "target_name": target_name,
                "graph_id": graph_id,
                "uuid": uuid.uuid4().hex,
                "props": props
            })

    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        """获取图谱统计信息"""
        # 节点数
        n_query = "MATCH (n {graph_id: $graph_id}) RETURN count(n) as count"
        n_res = self.neo4j.execute_read(n_query, {"graph_id": graph_id})
        node_count = n_res[0]["count"] if n_res else 0
        
        # 关系数
        e_query = "MATCH (n {graph_id: $graph_id})-[r]->() RETURN count(r) as count"
        e_res = self.neo4j.execute_read(e_query, {"graph_id": graph_id})
        edge_count = e_res[0]["count"] if e_res else 0
        
        # 实体类型
        t_query = "MATCH (n {graph_id: $graph_id}) RETURN DISTINCT labels(n) as labels"
        t_res = self.neo4j.execute_read(t_query, {"graph_id": graph_id})
        entity_types = []
        for row in t_res:
            entity_types.extend(row["labels"])
        entity_types = list(set(entity_types))
        
        return GraphInfo(
            graph_id=graph_id,
            node_count=node_count,
            edge_count=edge_count,
            entity_types=entity_types
        )

    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """获取完整图谱数据（前端可视化使用）"""
        # 获取节点
        # 使用 properties(n) 确保返回的是字典，避免 tuple/Node 对象兼容性问题
        n_query = "MATCH (n {graph_id: $graph_id}) RETURN properties(n) as n_props, labels(n) as labels"
        n_res = self.neo4j.execute_read(n_query, {"graph_id": graph_id})
        
        nodes_data = []
        for row in n_res:
            n = row["n_props"]
            nodes_data.append({
                "uuid": n.get("uuid"),
                "name": n.get("name"),
                "labels": row["labels"],
                "summary": n.get("summary", ""),
                "attributes": {k: v for k, v in n.items() if k not in ["uuid", "name", "summary", "graph_id", "created_at", "updated_at"]},
                "created_at": str(n.get("created_at", ""))
            })
            
        # 获取关系
        e_query = """
        MATCH (a {graph_id: $graph_id})-[r]->(b {graph_id: $graph_id}) 
        RETURN properties(r) as r_props, type(r) as type, a.uuid as source_uuid, b.uuid as target_uuid, a.name as source_name, b.name as target_name
        """
        e_res = self.neo4j.execute_read(e_query, {"graph_id": graph_id})
        
        edges_data = []
        for row in e_res:
            r = row["r_props"]
            edges_data.append({
                "uuid": r.get("uuid"),
                "name": row["type"],
                "fact": f"{row['source_name']} {row['type']} {row['target_name']}",
                "fact_type": row["type"],
                "source_node_uuid": row["source_uuid"],
                "target_node_uuid": row["target_uuid"],
                "source_node_name": row["source_name"],
                "target_node_name": row["target_name"],
                "attributes": {k: v for k, v in r.items() if k not in ["uuid", "graph_id", "created_at", "updated_at"]},
                "created_at": str(r.get("created_at", ""))
            })
            
        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }

    def delete_graph(self, graph_id: str):
        """删除图谱"""
        self.neo4j.clear_graph(graph_id)
