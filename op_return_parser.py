"""
OP_RETURN数据解析器
"""

import binascii
import re
import logging

logger = logging.getLogger(__name__)

class OpReturnParser:
    def __init__(self):
        # 定义区块链协议标识符和格式
        self.protocol_identifiers = {
            # Omni Layer协议 (原Mastercoin)
            b'omni': 'Omni',
            b'OMNI': 'Omni',
            
            # Counterparty协议
            b'CNTRPRTY': 'Counterparty',
            
            # BRC-20协议 (Bitcoin上的代币标准)
            b'{"p":"brc-20"': 'BRC-20',
            b'"p":"brc-20"': 'BRC-20',
            b'brc-20': 'BRC-20',
            b'BRC-20': 'BRC-20',
            
            # Ordinals协议
            b'ord': 'Ordinals',
            b'{"p":"ord"': 'Ordinals',
            
            # Taproot Assets (原Taro)
            b'taro': 'Taproot Assets',
            b'TARO': 'Taproot Assets',
            
            # RGB协议
            b'rgb': 'RGB',
            b'RGB': 'RGB',
            
            # Liquid Network
            b'liquid': 'Liquid',
            b'LIQUID': 'Liquid',
            
            # Rootstock (RSK)
            b'rsk': 'Rootstock',
            b'RSK': 'Rootstock',
            
            # Colored Coins
            b'cc': 'Colored Coins',
            b'CC': 'Colored Coins',
            
            # Open Assets
            b'OA': 'Open Assets',
            b'oa': 'Open Assets',
            
            # MEMO协议
            b'MEMO': 'MEMO',
            b'memo': 'MEMO',
            
            # Proof of Existence
            b'DOCPROOF': 'Proof of Existence',
            b'proof': 'Proof of Existence',
            
            # Timestamp协议
            b'TS': 'Timestamp',
            b'timestamp': 'Timestamp',
            
            # Bitcom协议族
            b'19HxigV4QyBv3tHpQVcUEQyq1pzZVdoAut': 'B://',  # B://协议
            b'1PuQa7K62MiKCtssSLKy1kh56WWU7MtUR5': 'BITFS', # BITFS协议
        }
        
        # 协议魔法数字 (前缀字节)
        self.protocol_magic_bytes = {
            # Omni Layer交易标识
            b'\x6f\x6d\x6e\x69': 'Omni',
            
            # Counterparty协议标识
            b'CNTRPRTY': 'Counterparty',
            
            # Colored Coins标识
            b'CC\x01\x00': 'Colored Coins',
            b'CC\x02\x00': 'Colored Coins',
        }
    
    def extract_op_return_data(self, transaction):
        """从交易中提取OP_RETURN数据"""
        op_return_outputs = []
        
        try:
            # 检查每个输出
            for i, vout in enumerate(transaction.get('vout', [])):
                script_pub_key = vout.get('scriptPubKey', {})
                
                # 检查是否为OP_RETURN类型
                if script_pub_key.get('type') == 'nulldata':
                    hex_data = script_pub_key.get('hex', '')
                    
                    if hex_data and hex_data.startswith('6a'):  # OP_RETURN操作码为0x6a
                        # 解析OP_RETURN数据
                        parsed_data = self._parse_op_return_hex(hex_data)
                        if parsed_data:
                            # 识别协议
                            protocol = self._identify_protocol(hex_data, parsed_data)
                            
                            op_return_outputs.append({
                                'vout_index': i,
                                'raw_data': hex_data,
                                'parsed_data': parsed_data,
                                'protocol': protocol,
                                'size': len(hex_data) // 2
                            })
                            
        except Exception as e:
            logger.error(f"解析交易OP_RETURN数据失败: {e}")
            
        return op_return_outputs
    
    def _parse_op_return_hex(self, hex_data):
        """解析OP_RETURN十六进制数据"""
        try:
            # 移除OP_RETURN操作码 (6a)
            if hex_data.startswith('6a'):
                hex_data = hex_data[2:]

            # 获取数据长度和实际数据
            if len(hex_data) >= 2:
                # 处理 OP_PUSHDATA1 (4c): 数据长度超过75字节时使用
                if hex_data[:2].lower() == '4c':
                    if len(hex_data) < 4:
                        return None
                    data_length = int(hex_data[2:4], 16)
                    actual_data = hex_data[4:]
                else:
                    # 第一个字节是数据长度 (直接push, 最多75字节)
                    data_length = int(hex_data[:2], 16)
                    actual_data = hex_data[2:]

                if len(actual_data) >= data_length * 2:
                    # 提取指定长度的数据
                    data_hex = actual_data[:data_length * 2]
                    return self._decode_text_data(data_hex)
                    
        except Exception as e:
            logger.error(f"解析OP_RETURN十六进制数据失败: {e}")
            
        return None
    
    def _decode_text_data(self, hex_data):
        """尝试将十六进制数据解码为文本"""
        try:
            # 转换为字节
            byte_data = binascii.unhexlify(hex_data)
            
            # 尝试不同的编码方式解码
            encodings = ['utf-8', 'ascii', 'latin-1', 'gbk', 'gb2312']
            
            for encoding in encodings:
                try:
                    decoded_text = byte_data.decode(encoding)
                    # 检查是否包含可读字符
                    if self._is_readable_text(decoded_text):
                        return {
                            'text': decoded_text,
                            'encoding': encoding,
                            'hex': hex_data
                        }
                except UnicodeDecodeError:
                    continue
                    
            # 如果无法解码为文本，返回原始十六进制
            return {
                'text': None,
                'encoding': None,
                'hex': hex_data,
                'note': 'Binary data, not text'
            }
            
        except Exception as e:
            logger.error(f"解码文本数据失败: {e}")
            return None
    
    def _is_readable_text(self, text):
        """检查文本是否可读"""
        if not text:
            return False
            
        # 计算可打印字符的比例
        printable_chars = 0
        total_chars = len(text)
        
        for char in text:
            # 检查是否为可打印字符（包括中文字符）
            if char.isprintable() or ord(char) > 127:
                printable_chars += 1
                
        # 如果可打印字符比例超过80%，认为是可读文本
        readable_ratio = printable_chars / total_chars if total_chars > 0 else 0
        
        # 同时检查是否包含明显的文本模式
        has_text_pattern = (
            re.search(r'[a-zA-Z\u4e00-\u9fff]{2,}', text) or  # 包含连续的字母或中文
            re.search(r'\d{4,}', text) or  # 包含4位以上数字
            any(keyword in text.lower() for keyword in ['http', 'www', 'bitcoin', 'btc'])
        )
        
        return readable_ratio >= 0.8 or (readable_ratio >= 0.5 and has_text_pattern)
    
    def _identify_protocol(self, hex_data, parsed_data):
        """识别OP_RETURN数据的协议类型"""
        try:
            # 转换十六进制数据为字节
            if hex_data.startswith('6a'):
                hex_data = hex_data[2:]  # 移除OP_RETURN操作码
            
            if len(hex_data) >= 2:
                data_length = int(hex_data[:2], 16)
                actual_data = hex_data[2:2 + data_length * 2]
                
                if actual_data:
                    byte_data = binascii.unhexlify(actual_data)
                    
                    # 1. 检查协议魔法数字 (最优先)
                    for magic_bytes, protocol_name in self.protocol_magic_bytes.items():
                        if byte_data.startswith(magic_bytes):
                            return protocol_name
                    
                    # 2. 检查Omni Layer协议 (特殊处理)
                    if self._is_omni_transaction(byte_data):
                        return 'Omni'
                    
                    # 3. 检查Counterparty协议 (特殊处理)
                    if self._is_counterparty_transaction(byte_data):
                        return 'Counterparty'
                    
                    # 4. 检查明确的协议标识符
                    for identifier, protocol_name in self.protocol_identifiers.items():
                        if identifier in byte_data:
                            return protocol_name
                    
                    # 5. 检查JSON格式的协议 (BRC-20, Ordinals等)
                    text = parsed_data.get('text', '') if parsed_data else ''
                    if text:
                        # BRC-20协议检测
                        if self._detect_brc20(text):
                            return 'BRC-20'
                        
                        # Ordinals协议检测
                        if self._detect_ordinals(text):
                            return 'Ordinals'
                        
                        # 其他JSON协议
                        if text.strip().startswith('{') and text.strip().endswith('}'):
                            try:
                                import json
                                data = json.loads(text)
                                if 'p' in data:  # 协议字段
                                    protocol = data['p'].lower()
                                    if protocol == 'brc-20':
                                        return 'BRC-20'
                                    elif protocol in ['ord', 'ordinals']:
                                        return 'Ordinals'
                                    elif protocol in ['tap', 'taproot']:
                                        return 'Taproot Assets'
                                    elif protocol == 'rgb':
                                        return 'RGB'
                                return 'JSON Protocol'
                            except:
                                pass
                    
                    # 6. 检查其他已知格式
                    if text:
                        text_lower = text.lower()
                        
                        # Open Assets协议
                        if 'open assets' in text_lower or text.startswith('OA'):
                            return 'Open Assets'
                        
                        # Colored Coins
                        if 'colored coin' in text_lower or text.startswith('CC'):
                            return 'Colored Coins'
                        
                        # Proof of Existence
                        if any(word in text_lower for word in ['proof', 'docproof', 'timestamp']):
                            return 'Proof of Existence'
                        
                        # 简单文本消息
                        if len(text) > 0 and len(text) <= 80 and text.isprintable():
                            return 'Text Message'
                    
                    # 7. 基于数据长度和特征的通用检测
                    data_len = len(byte_data)
                    
                    # 哈希值检测
                    if data_len == 32:
                        return 'Hash (SHA256)'
                    elif data_len == 20:
                        return 'Hash (SHA1/RIPEMD160)'
                    elif data_len == 16:
                        return 'Hash (MD5)'
                    
                    # 如果是可读文本但未识别协议
                    if parsed_data and parsed_data.get('text'):
                        return 'Unknown Text'
                    else:
                        return 'Unknown Binary'
            
            return 'Invalid Format'
                
        except Exception as e:
            logger.error(f"协议识别失败: {e}")
            return 'Parse Error'
    
    def _is_omni_transaction(self, byte_data):
        """检测是否为Omni Layer交易"""
        # Omni Layer使用"omni"作为标识，或者特定的字节序列
        if len(byte_data) >= 4:
            # 检查是否包含omni标识
            if b'omni' in byte_data or b'OMNI' in byte_data:
                return True
            # 检查Omni的魔法字节序列
            if byte_data[:4] == b'\x6f\x6d\x6e\x69':  # "omni" in hex
                return True
        return False
    
    def _is_counterparty_transaction(self, byte_data):
        """检测是否为Counterparty交易"""
        # Counterparty使用"CNTRPRTY"标识
        if b'CNTRPRTY' in byte_data:
            return True
        # 检查Counterparty的其他标识模式
        if len(byte_data) >= 8 and byte_data.startswith(b'CNTRPRTY'):
            return True
        return False
    
    def _detect_brc20(self, text):
        """检测BRC-20协议"""
        text_lower = text.lower()
        # BRC-20通常是JSON格式，包含特定字段
        if 'brc-20' in text_lower or 'brc20' in text_lower:
            return True
        if '"p":"brc-20"' in text_lower:
            return True
        # 检查BRC-20的典型JSON结构
        if all(field in text_lower for field in ['"p":', '"op":', '"tick":']):
            return True
        return False
    
    def _detect_ordinals(self, text):
        """检测Ordinals协议"""
        text_lower = text.lower()
        if 'ordinals' in text_lower or '"p":"ord"' in text_lower:
            return True
        # 检查Ordinals的典型结构
        if '"inscription"' in text_lower or '"ord"' in text_lower:
            return True
        return False