"""
配置文件模板 - 复制此文件为 config.py 并填写实际配置
"""

# Bitcoin节点配置
BITCOIN_RPC_USER = "your_rpc_username"
BITCOIN_RPC_PASSWORD = "your_rpc_password"
BITCOIN_RPC_HOST = "127.0.0.1"
BITCOIN_RPC_PORT = 8332

# MySQL数据库配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'your_db_username',
    'password': 'your_db_password',
    'database': 'bitcoin_op_return',
    'charset': 'utf8mb4'
}

# 扫描配置
BATCH_SIZE = 100  # 每批处理的区块数量
SLEEP_TIME = 0.3  # 请求间隔时间（秒）

# RPC连接配置
RPC_MAX_RETRIES = 3  # 最大重试次数
RPC_BASE_DELAY = 1.0  # 基础延迟时间（秒）
