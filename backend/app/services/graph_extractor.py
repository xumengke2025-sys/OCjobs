import json
import re
from typing import List, Dict, Any, Optional
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger('mirofish.services.graph_extractor')

class GraphExtractor:
    """使用 LLM 从文本中提取图谱数据（节点和关系）"""
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def extract(self, text: str) -> Dict[str, Any]:
        """
        从文本中提取实体和关系。
        返回格式:
        {
            "nodes": [{"name": "...", "label": "...", "summary": "...", "properties": {...}}],
            "edges": [{"from": "...", "to": "...", "relationship": "...", "properties": {...}}]
        }
        """
        prompt = f"""
        你是一个专业的知识图谱构建专家。请从以下文本中提取关键实体（Nodes）和它们之间的关系（Edges）。
        
        提取规则：
        1. 节点（Nodes）必须包含：name (名称), label (类型，如 Person, Organization, Location, Event, Concept), summary (一句话简介)。
        2. 关系（Edges）必须包含：from (源节点名称), to (目标节点名称), relationship (关系类型，如 WorksAt, LocatedIn, ParticipatedIn)。
        3. 尽量提取详细的属性信息并放入 properties 字典中。
        4. 仅返回 JSON 格式数据，不要有任何解释。
        
        待处理文本：
        {text}
        
        JSON 格式要求：
        {{
            "nodes": [
                {{"name": "实体名", "label": "类型", "summary": "简介", "properties": {{}}}}
            ],
            "edges": [
                {{"from": "源实体", "to": "目标实体", "relationship": "关系名", "properties": {{}}}}
            ]
        }}
        """
        
        try:
            result = self.llm_client.chat_json(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON knowledge graphs."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            logger.info(f"Successfully extracted {len(result.get('nodes', []))} nodes and {len(result.get('edges', []))} edges")
            return result
        except Exception as e:
            logger.error(f"Error extracting graph from text: {e}")
            return {"nodes": [], "edges": []}
