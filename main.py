#!/usr/bin/env python3
"""
Bitcoin OP_RETURN数据收集器 - 主程序
"""

import argparse
import logging
import sys
from block_scanner import BlockScanner
from bitcoin_client import BitcoinClient
from database import Database

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('op_return_scanner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_connections():
    """测试所有连接"""
    logger.info("正在测试连接...")
    
    # 测试Bitcoin节点连接
    try:
        bitcoin_client = BitcoinClient()
        if not bitcoin_client.test_connection():
            logger.error("Bitcoin节点连接失败")
            return False
    except Exception as e:
        logger.error(f"Bitcoin节点连接测试失败: {e}")
        return False
    
    # 测试数据库连接
    try:
        database = Database()
        logger.info("数据库连接成功")
        database.disconnect()
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        return False
    
    logger.info("所有连接测试通过")
    return True

def show_statistics():
    """显示扫描统计信息"""
    try:
        scanner = BlockScanner()
        stats = scanner.get_scan_statistics()
        
        if stats:
            print("\n=== 扫描统计信息 ===")
            print(f"当前区块高度: {stats['current_block_height']:,}")
            print(f"已扫描区块: {stats['last_scanned_block']:,}")
            print(f"剩余区块: {stats['blocks_remaining']:,}")
            print(f"扫描进度: {stats['scan_progress']:.2f}%")
            print(f"总OP_RETURN记录: {stats['total_op_return_records']:,}")
            print(f"包含文字的记录: {stats['text_op_return_records']:,}")
            
            # 显示最新的几条记录
            database = Database()
            latest_records = database.get_latest_records(5)
            
            if latest_records:
                print("\n=== 最新发现的文字记录 ===")
                for record in latest_records:
                    protocol = record.get('protocol_name', 'Unknown')
                    print(f"区块 {record['block_height']} | {record['txid'][:16]}... | [{protocol}] | {record['decoded_text'][:50]}...")
            
            # 显示协议统计
            protocol_stats = database.get_protocol_statistics()
            if protocol_stats:
                print("\n=== 协议统计 (Top 10) ===")
                for stat in protocol_stats[:10]:
                    print(f"{stat['protocol_name']}: {stat['count']:,} 条记录")
            
            database.disconnect()
        else:
            print("无法获取统计信息")
            
    except Exception as e:
        logger.error(f"显示统计信息失败: {e}")

def scan_range(start_block, end_block):
    """扫描指定区块范围"""
    try:
        scanner = BlockScanner()
        scanner.scan_blocks(start_block, end_block)
        logger.info(f"区块范围 {start_block}-{end_block} 扫描完成")
        
    except Exception as e:
        logger.error(f"扫描区块范围失败: {e}")

def scan_latest(num_blocks):
    """扫描最新的区块"""
    try:
        scanner = BlockScanner()
        scanner.scan_latest_blocks(num_blocks)
        logger.info(f"最新 {num_blocks} 个区块扫描完成")
        
    except Exception as e:
        logger.error(f"扫描最新区块失败: {e}")

def scan_all():
    """扫描所有区块"""
    try:
        scanner = BlockScanner()
        scanner.scan_from_genesis()
        logger.info("全量扫描完成")
        
    except Exception as e:
        logger.error(f"全量扫描失败: {e}")

def show_protocol_records(protocol_name):
    """显示指定协议的记录"""
    try:
        database = Database()
        records = database.get_records_by_protocol(protocol_name, 20)
        
        if records:
            print(f"\n=== {protocol_name} 协议记录 ===")
            for record in records:
                print(f"区块 {record['block_height']} | {record['txid'][:16]}... | {record['decoded_text'][:80]}...")
        else:
            print(f"未找到 {protocol_name} 协议的记录")
            
        database.disconnect()
        
    except Exception as e:
        logger.error(f"显示协议记录失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='Bitcoin OP_RETURN数据收集器')
    parser.add_argument('--test', action='store_true', help='测试连接')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--scan-range', nargs=2, type=int, metavar=('START', 'END'), 
                       help='扫描指定区块范围')
    parser.add_argument('--scan-latest', type=int, metavar='NUM', 
                       help='扫描最新的N个区块')
    parser.add_argument('--scan-all', action='store_true', help='扫描所有区块（从上次停止处继续）')
    parser.add_argument('--protocol', type=str, metavar='NAME', help='查看指定协议的记录')
    
    args = parser.parse_args()
    
    # 如果没有参数，显示帮助
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    try:
        if args.test:
            if test_connections():
                print("✅ 所有连接测试通过")
            else:
                print("❌ 连接测试失败")
                sys.exit(1)
                
        elif args.stats:
            show_statistics()
            
        elif args.scan_range:
            start_block, end_block = args.scan_range
            logger.info(f"开始扫描区块范围: {start_block} 到 {end_block}")
            scan_range(start_block, end_block)
            
        elif args.scan_latest:
            logger.info(f"开始扫描最新 {args.scan_latest} 个区块")
            scan_latest(args.scan_latest)
            
        elif args.scan_all:
            logger.info("开始全量扫描")
            scan_all()
            
        elif args.protocol:
            show_protocol_records(args.protocol)
            
    except KeyboardInterrupt:
        logger.info("用户中断扫描")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()