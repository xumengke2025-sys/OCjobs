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
    print("🚀 正在启动 万年 后端服务...")
    print(f"📂 当前工作目录: {os.getcwd()}")
    
    # 检查 .env 文件是否存在
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../.env')
    if os.path.exists(env_path):
        print(f"✅ 找到配置文件: {env_path}")
    else:
        print(f"⚠️ 未找到 .env 文件: {env_path}")

    # 验证配置
    errors = Config.validate()
    if errors:
        print("\n❌ 启动失败: 配置检查未通过")
        for err in errors:
            print(f"  - {err}")
        print("\n请确保根目录下的 .env 文件已正确配置 LLM_API_KEY。")
        print("="*50 + "\n")
        sys.exit(1)
    
    # 创建应用
    try:
        app = create_app()
        print("✅ Flask 应用初始化成功")
    except Exception as e:
        print(f"❌ Flask 应用初始化失败: {str(e)}")
        sys.exit(1)
    
    # 获取运行配置
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5002))
    
    print(f"📡 服务将运行在: http://{host}:{port}")
    print("="*50 + "\n")
    
    # 启动服务
    app.run(host=host, port=port, debug=Config.DEBUG, threaded=True, use_reloader=False)


if __name__ == '__main__':
    main()

