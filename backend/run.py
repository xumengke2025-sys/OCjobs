"""
万年 Backend 启动入口
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config


def main():
    """主函数"""
    print("\n" + "="*50)
    print("Starting Wannian Backend Service...")
    print(f"Current Working Directory: {os.getcwd()}")
    
    # 检查 .env 文件是否存在
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../.env')
    if os.path.exists(env_path):
        print(f"Found Config: {env_path}")
    else:
        print(f"Config Not Found: {env_path}")

    # 验证配置 (改为仅警告，不阻塞启动)
    errors = Config.validate()
    if errors:
        print("\n⚠️  Configuration Warning: Some API keys are missing")
        for err in errors:
            print(f"  - {err}")
        print("The server will start, but fortune analysis will require configuration in .env")
        print("="*50 + "\n")
    else:
        print("✅ Config validation passed")
    
    # 创建应用
    try:
        app = create_app()
        print("Flask App initialized successfully")
    except Exception as e:
        print(f"Flask App initialization failed: {str(e)}")
        sys.exit(1)
    
    # 获取运行配置
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5002))
    
    print(f"Service running at: http://{host}:{port}")
    print("="*50 + "\n")
    
    # 启动服务
    app.run(host=host, port=port, debug=Config.DEBUG, threaded=True, use_reloader=False)


if __name__ == '__main__':
    main()

