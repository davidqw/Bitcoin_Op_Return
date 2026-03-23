# Bitcoin OP_RETURN 数据收集器

这是一个用于扫描Bitcoin区块链中OP_RETURN数据并提取其中文字信息的工具。

## 功能特性

- 连接本地Bitcoin节点获取区块数据
- 解析OP_RETURN输出中的文字数据
- 智能识别常见协议类型（MEMO、Pump Token、价格信息等）
- 支持多种字符编码（UTF-8, ASCII, GBK等）
- 批量处理和数据库存储
- 断点续传功能
- 扫描进度跟踪
- 协议统计和分类查看

## 环境要求

- Python 3.7+
- MySQL 5.7+
- Bitcoin Core节点（已同步）

## 安装和配置

### 1. 修改配置文件

编辑 `config.py` 文件，修改以下配置：

```python
# Bitcoin节点配置（已配置）
BITCOIN_RPC_USER = "YourRPCUsername"
BITCOIN_RPC_PASSWORD = "YourRPCPassword"
BITCOIN_RPC_PORT = 8332

# MySQL数据库配置（需要修改）
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'your_mysql_user',      # 修改为你的MySQL用户名
    'password': 'your_mysql_password', # 修改为你的MySQL密码
    'database': 'bitcoin_op_return',
    'charset': 'utf8mb4'
}
```

### 2. 运行安装脚本

```bash
python setup.py
```

这个脚本会：
- 安装Python依赖包
- 创建MySQL数据库和表结构
- 测试Bitcoin节点连接

## 使用方法

### 测试连接
```bash
python main.py --test
```

### 查看统计信息
```bash
python main.py --stats
```

### 扫描最新区块
```bash
# 扫描最新100个区块
python main.py --scan-latest 100
```

### 扫描指定区块范围
```bash
# 扫描区块700000到700100
python main.py --scan-range 700000 700100
```

### 全量扫描
```bash
# 从上次停止的位置继续扫描到最新区块
python main.py --scan-all
```

### 查看特定协议记录
```bash
# 查看Omni协议记录
python main.py --protocol "Omni"

# 查看Counterparty协议记录
python main.py --protocol "Counterparty"

# 查看BRC-20代币记录
python main.py --protocol "BRC-20"

# 查看Ordinals协议记录
python main.py --protocol "Ordinals"

# 查看文本消息
python main.py --protocol "Text Message"
```

## 数据库结构

### op_return_data表
存储OP_RETURN数据的主表：
- `block_height`: 区块高度
- `txid`: 交易ID
- `vout_index`: 输出索引
- `raw_data`: 原始十六进制数据
- `decoded_text`: 解析出的文字内容
- `protocol_name`: 协议类型（如：Omni、Counterparty、BRC-20、Ordinals等）
- `data_size`: 数据大小

### scan_progress表
记录扫描进度：
- `last_scanned_block`: 最后扫描的区块高度

## 日志文件

程序运行日志保存在 `op_return_scanner.log` 文件中。

## 支持的协议类型

系统能够自动识别以下区块链协议：

### 主要区块链协议
- **Omni Layer**: Omni协议（原Mastercoin），用于在Bitcoin上发行代币
- **Counterparty**: Counterparty协议，支持资产发行和智能合约
- **BRC-20**: Bitcoin上的代币标准，类似于以太坊的ERC-20
- **Ordinals**: Bitcoin序数协议，用于NFT和铭文
- **Taproot Assets**: Taproot资产协议（原Taro）
- **RGB**: RGB协议，用于智能合约和代币
- **Colored Coins**: 有色币协议
- **Open Assets**: 开放资产协议

### 其他协议类型
- **Liquid Network**: Liquid侧链相关
- **Rootstock (RSK)**: RSK侧链相关
- **B:// / BITFS**: Bitcom协议族
- **MEMO**: 文本消息协议
- **Proof of Existence**: 存在性证明协议
- **Timestamp**: 时间戳协议
- **Hash**: 各种哈希值（SHA256、SHA1、MD5等）
- **Text Message**: 普通文本消息
- **JSON Protocol**: JSON格式的协议数据

## 注意事项

1. 确保Bitcoin节点已完全同步
2. 首次全量扫描可能需要较长时间
3. 建议在磁盘空间充足的环境下运行
4. 可以随时中断和恢复扫描过程
5. 新增的protocol_name字段需要运行迁移脚本：`mysql -u root -p < migrate_add_protocol.sql`