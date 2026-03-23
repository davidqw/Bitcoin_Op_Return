"""
Bitcoin RPC客户端
"""

from bitcoinrpc.authproxy import AuthServiceProxy
import logging
from config import BITCOIN_RPC_USER, BITCOIN_RPC_PASSWORD, BITCOIN_RPC_HOST, BITCOIN_RPC_PORT

logger = logging.getLogger(__name__)

class BitcoinClient:
    def __init__(self):
        rpc_url = f"http://{BITCOIN_RPC_USER}:{BITCOIN_RPC_PASSWORD}@{BITCOIN_RPC_HOST}:{BITCOIN_RPC_PORT}"
        self.rpc = AuthServiceProxy(rpc_url)
        
    def get_block_count(self):
        """获取当前区块高度"""
        try:
            return self.rpc.getblockcount()
        except Exception as e:
            logger.error(f"获取区块高度失败: {e}")
            raise
            
    def get_block_hash(self, height):
        """根据高度获取区块哈希"""
        try:
            return self.rpc.getblockhash(height)
        except Exception as e:
            logger.error(f"获取区块哈希失败，高度: {height}, 错误: {e}")
            raise
            
    def get_block(self, block_hash):
        """获取区块详细信息"""
        try:
            return self.rpc.getblock(block_hash, 2)  # verbosity=2 包含交易详情
        except Exception as e:
            logger.error(f"获取区块详情失败，哈希: {block_hash}, 错误: {e}")
            raise
            
    def get_raw_transaction(self, txid):
        """获取原始交易数据"""
        try:
            return self.rpc.getrawtransaction(txid, True)
        except Exception as e:
            logger.error(f"获取交易详情失败，txid: {txid}, 错误: {e}")
            return None
            
    def test_connection(self):
        """测试连接"""
        try:
            info = self.rpc.getblockchaininfo()
            logger.info(f"Bitcoin节点连接成功，当前区块: {info['blocks']}")
            return True
        except Exception as e:
            logger.error(f"Bitcoin节点连接失败: {e}")
            return False