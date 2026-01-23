
import sys
import os

# 将 backend 目录添加到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.utils.neo4j_client import Neo4jClient
from app.config import Config

def test_neo4j_connection():
    print("Testing Neo4j connection...")
    try:
        client = Neo4jClient()
        print(f"Connected to Neo4j at {Config.NEO4J_URI} (Database: {Config.NEO4J_DATABASE})")
        
        # 测试写操作
        print("Testing write operation...")
        write_query = "MERGE (n:TestNode {id: 'test_1'}) SET n.name = 'Connection Test' RETURN n"
        result = client.execute_query(write_query)
        print(f"Write result: {result}")
        
        # 测试读操作
        print("Testing read operation...")
        read_query = "MATCH (n:TestNode {id: 'test_1'}) RETURN n"
        result = client.execute_read(read_query)
        print(f"Read result: {result}")
        
        # 清理
        print("Cleaning up test node...")
        delete_query = "MATCH (n:TestNode {id: 'test_1'}) DETACH DELETE n"
        client.execute_query(delete_query)
        print("Cleanup successful.")
        
        print("\nNeo4j connection and basic operations verified successfully!")
        return True
    except Exception as e:
        print(f"\nNeo4j test failed: {e}")
        print("\nPlease ensure Neo4j is running locally and credentials in .env are correct.")
        return False

if __name__ == "__main__":
    test_neo4j_connection()
