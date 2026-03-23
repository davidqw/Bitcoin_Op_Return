#!/usr/bin/env python3
"""
安装和设置脚本
"""

import subprocess
import sys
import os
import mysql.connector
from config import MYSQL_CONFIG

def install_dependencies():
    """安装Python依赖"""
    print("正在安装Python依赖...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Python依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Python依赖安装失败: {e}")
        return False

def setup_database():
    """设置数据库"""
    print("正在设置数据库...")
    try:
        # 创建数据库连接（不指定database）
        config = MYSQL_CONFIG.copy()
        database_name = config.pop('database')
        
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # 读取并执行SQL文件
        with open('database_setup.sql', 'r', encoding='utf-8') as f:
            sql_commands = f.read()
        
        # 执行SQL命令
        for command in sql_commands.split(';'):
            command = command.strip()
            if command:
                cursor.execute(command)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ 数据库设置完成")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ 数据库设置失败: {e}")
        return False
    except FileNotFoundError:
        print("❌ 找不到database_setup.sql文件")
        return False

def check_bitcoin_connection():
    """检查Bitcoin节点连接"""
    print("正在检查Bitcoin节点连接...")
    try:
        from bitcoin_client import BitcoinClient
        client = BitcoinClient()
        if client.test_connection():
            print("✅ Bitcoin节点连接正常")
            return True
        else:
            print("❌ Bitcoin节点连接失败")
            return False
    except Exception as e:
        print(f"❌ Bitcoin节点连接检查失败: {e}")
        return False

def main():
    print("=== Bitcoin OP_RETURN数据收集器 - 安装设置 ===\n")
    
    success = True
    
    # 安装依赖
    if not install_dependencies():
        success = False
    
    print()
    
    # 设置数据库
    if not setup_database():
        success = False
    
    print()
    
    # 检查Bitcoin连接
    if not check_bitcoin_connection():
        success = False
    
    print("\n" + "="*50)
    
    if success:
        print("✅ 安装设置完成！")
        print("\n使用方法:")
        print("  python main.py --test          # 测试连接")
        print("  python main.py --stats         # 显示统计信息") 
        print("  python main.py --scan-latest 100  # 扫描最新100个区块")
        print("  python main.py --scan-all      # 扫描所有区块")
        print("  python main.py --scan-range 700000 700100  # 扫描指定范围")
    else:
        print("❌ 安装设置失败，请检查配置")
        sys.exit(1)

if __name__ == '__main__':
    main()