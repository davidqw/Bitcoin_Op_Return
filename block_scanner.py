"""
区块扫描器
"""

import time
import logging
from bitcoin_client import BitcoinClient
from op_return_parser import OpReturnParser
from database import Database
from config import BATCH_SIZE, SLEEP_TIME

logger = logging.getLogger(__name__)

class BlockScanner:
    def __init__(self):
        self.bitcoin_client = BitcoinClient()
        self.parser = OpReturnParser()
        self.database = Database()
        
    def scan_blocks(self, start_block=None, end_block=None):
        """扫描区块范围"""
        try:
            # 获取当前最高区块
            current_block = self.bitcoin_client.get_block_count()
            
            # 确定起始区块
            if start_block is None:
                start_block = self.database.get_last_scanned_block() + 1
                
            # 确定结束区块
            if end_block is None:
                end_block = current_block
                
            logger.info(f"开始扫描区块范围: {start_block} 到 {end_block}")
            
            # 分批处理
            for batch_start in range(start_block, end_block + 1, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE - 1, end_block)
                
                logger.info(f"处理区块批次: {batch_start} 到 {batch_end}")
                
                batch_data = []
                
                # 扫描当前批次的区块
                for block_height in range(batch_start, batch_end + 1):
                    try:
                        op_return_data = self._scan_single_block(block_height)
                        batch_data.extend(op_return_data)
                        
                        # 控制请求频率
                        time.sleep(SLEEP_TIME)
                        
                    except Exception as e:
                        logger.error(f"扫描区块 {block_height} 失败: {e}")
                        continue
                
                # 批量保存数据
                if batch_data:
                    saved_count = self.database.batch_save_op_return_data(batch_data)
                    logger.info(f"批次 {batch_start}-{batch_end}: 发现 {len(batch_data)} 条OP_RETURN数据，保存 {saved_count} 条新数据")
                
                # 更新扫描进度
                self.database.update_scan_progress(batch_end)
                
                # 输出进度统计
                progress = ((batch_end - start_block + 1) / (end_block - start_block + 1)) * 100
                logger.info(f"扫描进度: {progress:.2f}% ({batch_end}/{end_block})")
                
        except Exception as e:
            logger.error(f"扫描区块失败: {e}")
            raise
    
    def _scan_single_block(self, block_height):
        """扫描单个区块"""
        op_return_data = []
        
        try:
            # 获取区块哈希
            block_hash = self.bitcoin_client.get_block_hash(block_height)
            
            # 获取区块数据
            block = self.bitcoin_client.get_block(block_hash)
            
            # 检查每个交易
            for tx in block.get('tx', []):
                txid = tx.get('txid')
                
                # 解析OP_RETURN数据
                op_returns = self.parser.extract_op_return_data(tx)
                
                for op_return in op_returns:
                    op_return_data.append({
                        'block_height': block_height,
                        'txid': txid,
                        'vout_index': op_return['vout_index'],
                        'raw_data': op_return['raw_data'],
                        'parsed_data': op_return['parsed_data'],
                        'protocol': op_return.get('protocol', 'Unknown'),
                        'data_size': op_return['size']
                    })
                    
        except Exception as e:
            logger.error(f"扫描区块 {block_height} 失败: {e}")
            
        return op_return_data
    
    def scan_latest_blocks(self, num_blocks=100):
        """扫描最新的区块"""
        try:
            current_block = self.bitcoin_client.get_block_count()
            start_block = max(1, current_block - num_blocks + 1)
            
            self.scan_blocks(start_block, current_block)
            
        except Exception as e:
            logger.error(f"扫描最新区块失败: {e}")
            raise
    
    def scan_from_genesis(self):
        """从创世区块开始扫描"""
        try:
            last_scanned = self.database.get_last_scanned_block()
            start_block = max(1, last_scanned + 1)
            
            logger.info(f"从区块 {start_block} 开始扫描到最新区块")
            self.scan_blocks(start_block)
            
        except Exception as e:
            logger.error(f"从创世区块扫描失败: {e}")
            raise
    
    def get_scan_statistics(self):
        """获取扫描统计信息"""
        try:
            current_block = self.bitcoin_client.get_block_count()
            last_scanned = self.database.get_last_scanned_block()
            total_records = self.database.get_op_return_count()
            text_records = self.database.get_text_op_return_count()
            
            return {
                'current_block_height': current_block,
                'last_scanned_block': last_scanned,
                'blocks_remaining': current_block - last_scanned,
                'total_op_return_records': total_records,
                'text_op_return_records': text_records,
                'scan_progress': (last_scanned / current_block * 100) if current_block > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"获取扫描统计失败: {e}")
            return None