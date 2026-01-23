from neo4j import GraphDatabase
from typing import Dict, Any, List, Optional
import threading
from ..config import Config
from .logger import get_logger

logger = get_logger('mirofish.utils.neo4j_client')

class Neo4jClient:
    """Neo4j 数据库单例客户端"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Neo4jClient, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.uri = Config.NEO4J_URI
        self.user = Config.NEO4J_USER
        self.password = Config.NEO4J_PASSWORD
        self.database = Config.NEO4J_DATABASE
        
        if not all([self.uri, self.user, self.password]):
            logger.error("Neo4j 配置缺失，请检查环境变量")
            self.driver = None
            return
            
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # 延迟验证连接，或者在第一次使用时验证
            self._initialized = True
            logger.info(f"Neo4j client initialized with URI: {self.uri}")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {e}")
            self.driver = None

    def _verify_connection(self):
        """验证连接，如果失败则抛出清晰的错误"""
        if not self.driver:
            raise ConnectionError("Neo4j 驱动未初始化，请检查配置。")
        try:
            self.driver.verify_connectivity()
        except Exception as e:
            logger.error(f"Neo4j 连接验证失败: {e}")
            raise ConnectionError(f"无法连接到 Neo4j 数据库 ({self.uri})。请确保 Neo4j 服务已启动并可以访问。具体错误: {str(e)}")

    def close(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """执行写操作"""
        self._verify_connection()
        with self.driver.session(database=self.database) as session:
            return session.execute_write(lambda tx: tx.run(query, parameters).data())

    def execute_read(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """执行读操作"""
        self._verify_connection()
        with self.driver.session(database=self.database) as session:
            return session.execute_read(lambda tx: tx.run(query, parameters).data())

    def clear_graph(self, graph_id: str):
        """清除特定图谱的数据"""
        query = "MATCH (n {graph_id: $graph_id}) DETACH DELETE n"
        self.execute_query(query, {"graph_id": graph_id})
