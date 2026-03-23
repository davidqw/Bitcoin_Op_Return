"""
数据库操作类
"""

import mysql.connector
from mysql.connector import Error
import logging
import json
from config import MYSQL_CONFIG

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(**MYSQL_CONFIG)
            if self.connection.is_connected():
                logger.info("MySQL数据库连接成功")
        except Error as e:
            logger.error(f"MySQL数据库连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL数据库连接已关闭")
    
    def get_last_scanned_block(self):
        """获取上次扫描的区块高度"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT last_scanned_block FROM scan_progress ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else 0
            
        except Error as e:
            logger.error(f"获取扫描进度失败: {e}")
            return 0
    
    def update_scan_progress(self, block_height):
        """更新扫描进度"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """UPDATE scan_progress 
                   SET last_scanned_block = %s, updated_at = NOW() 
                   WHERE id = (SELECT id FROM (SELECT id FROM scan_progress ORDER BY id DESC LIMIT 1) t)""",
                (block_height,)
            )
            self.connection.commit()
            cursor.close()
            
        except Error as e:
            logger.error(f"更新扫描进度失败: {e}")
            raise
    
    def save_op_return_data(self, block_height, txid, vout_index, raw_data, parsed_data, protocol, data_size):
        """保存OP_RETURN数据"""
        try:
            cursor = self.connection.cursor()
            
            # 准备解析后的文本数据
            decoded_text = None
            if parsed_data and parsed_data.get('text'):
                decoded_text = parsed_data['text']
            
            # 插入数据，如果已存在则忽略
            cursor.execute(
                """INSERT IGNORE INTO op_return_data 
                   (block_height, txid, vout_index, raw_data, decoded_text, protocol_name, data_size)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (block_height, txid, vout_index, raw_data, decoded_text, protocol, data_size)
            )
            
            self.connection.commit()
            row_count = cursor.rowcount
            cursor.close()

            return row_count > 0
            
        except Error as e:
            logger.error(f"保存OP_RETURN数据失败: {e}")
            return False
    
    def batch_save_op_return_data(self, data_list):
        """批量保存OP_RETURN数据"""
        if not data_list:
            return 0
            
        try:
            cursor = self.connection.cursor()
            
            # 准备批量插入的数据
            insert_data = []
            for item in data_list:
                decoded_text = None
                if item['parsed_data'] and item['parsed_data'].get('text'):
                    decoded_text = item['parsed_data']['text']
                
                insert_data.append((
                    item['block_height'],
                    item['txid'], 
                    item['vout_index'],
                    item['raw_data'],
                    decoded_text,
                    item.get('protocol', 'Unknown'),
                    item['data_size']
                ))
            
            # 批量插入
            cursor.executemany(
                """INSERT IGNORE INTO op_return_data 
                   (block_height, txid, vout_index, raw_data, decoded_text, protocol_name, data_size)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                insert_data
            )
            
            self.connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            
            return affected_rows
            
        except Error as e:
            logger.error(f"批量保存OP_RETURN数据失败: {e}")
            return 0
    
    def get_op_return_count(self):
        """获取OP_RETURN记录总数"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM op_return_data")
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else 0
            
        except Error as e:
            logger.error(f"获取OP_RETURN记录数量失败: {e}")
            return 0
    
    def get_text_op_return_count(self):
        """获取包含文字的OP_RETURN记录数量"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM op_return_data WHERE decoded_text IS NOT NULL AND decoded_text != ''")
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] if result else 0
            
        except Error as e:
            logger.error(f"获取文字OP_RETURN记录数量失败: {e}")
            return 0
    
    def get_latest_records(self, limit=10):
        """获取最新的记录"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT block_height, txid, decoded_text, protocol_name, data_size, created_at 
                   FROM op_return_data 
                   WHERE decoded_text IS NOT NULL 
                   ORDER BY block_height DESC, created_at DESC 
                   LIMIT %s""",
                (limit,)
            )
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Error as e:
            logger.error(f"获取最新记录失败: {e}")
            return []
    
    def get_protocol_statistics(self):
        """获取协议统计信息"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT protocol_name, COUNT(*) as count 
                   FROM op_return_data 
                   WHERE protocol_name IS NOT NULL 
                   GROUP BY protocol_name 
                   ORDER BY count DESC 
                   LIMIT 20"""
            )
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Error as e:
            logger.error(f"获取协议统计失败: {e}")
            return []
    
    def get_records_by_protocol(self, protocol_name, limit=10):
        """按协议获取记录"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT block_height, txid, decoded_text, protocol_name, data_size, created_at 
                   FROM op_return_data 
                   WHERE protocol_name = %s AND decoded_text IS NOT NULL 
                   ORDER BY block_height DESC 
                   LIMIT %s""",
                (protocol_name, limit)
            )
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Error as e:
            logger.error(f"按协议获取记录失败: {e}")
            return []