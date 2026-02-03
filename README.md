# 算法竞赛补题自动收集与排序系统

自动收集你在各平台（Codeforces / AtCoder / LeetCode）"尝试了未解决的题目"以及参与的比赛中”未尝试的题目“，结合 Clist 的难度评级，统一排序并输出训练清单。

## 功能特性

- 支持多平台爬取：Codeforces、AtCoder、LeetCode
- 自动获取 Clist 难度评级
- 按难度排序并导出
- 支持多种导出格式：JSON、CSV、Markdown

## 项目结构

```
.
├── crawlers/              # 爬虫模块
│   ├── codeforces.py     # Codeforces爬虫
│   ├── atcoder.py        # AtCoder爬虫
│   └── leetcode.py       # LeetCode爬虫
├── clist/                # Clist集成
│   └── fetcher.py        # Rating获取器
├── models/               # 数据模型
│   └── problem.py        # 题目数据模型
├── exporter/             # 导出模块
│   └── export.py         # 排序与导出
├── config.yaml           # 配置文件
├── main.py              # 主程序入口
├── pyproject.toml       # 项目配置（uv）
└── requirements.txt     # 依赖列表（pip）
```

## 安装依赖

### 使用 uv（推荐）

```bash
# 安装 uv（如果还没安装）
pip install uv

# 同步依赖
uv sync

# 运行程序
uv run python main.py
```

### 使用 pip（传统方式）

```bash
pip install -r requirements.txt
python main.py
```

## 配置说明

编辑 `config.yaml` 文件，填入您的账号信息：

### Codeforces 配置

```yaml
platforms:
  codeforces:
    enabled: true
    handle: "your_username"  # 您的Codeforces用户名
    include_gym: true        # 是否包含Gym题目
```

### AtCoder 配置

```yaml
  atcoder:
    enabled: true
    handle: "your_username"  # 您的AtCoder用户名
    contest_only: true       # 是否只爬取比赛题目
```

### LeetCode 配置

```yaml
  leetcode:
    enabled: true
    cookies:
      LEETCODE_SESSION: "your_session_token"
      csrftoken: "your_csrf_token"
```

**如何获取 LeetCode Cookies：**
1. 打开浏览器，登录 LeetCode
2. 按 F12 打开开发者工具
3. 进入 Application/存储 → Cookies
4. 找到 `LEETCODE_SESSION` 和 `csrftoken`，复制其值

### Clist API 配置

```yaml
clist:
  api_key: "your_api_key"  # 您的Clist API Key
```

## 使用方法

### 使用 uv

```bash
uv run python main.py
```

### 使用 pip

```bash
python main.py
```

程序会自动：
1. 爬取各平台未解决题目
2. 获取 Clist 难度评级
3. 按难度排序
4. 导出到 `output/` 目录

## 输出文件

运行后会在 `output/` 目录生成三个文件：

- `problems.json` - 机器可读的JSON格式
- `problems.csv` - Excel可打开的表格格式
- `README.md` - 可读性好的训练清单表格

## 注意事项

1. **Codeforces**: 使用官方API，无需登录，支持大量提交记录
2. **AtCoder**: 使用AtCoder Problems API，爬取比赛题目
3. **LeetCode**: 需要提供登录Cookie，基于最近提交记录
4. **Clist**: 需要API Key，如不配置则跳过rating获取

## 故障排除

### Codeforces 爬取失败
- 检查用户名是否正确
- 确认网络连接正常

### AtCoder 爬取失败
- 确认用户名正确
- 检查是否有参赛记录

### LeetCode 爬取失败
- 确认Cookie未过期
- 重新获取Cookie并更新配置

### Clist Rating 获取失败
- 检查API Key是否正确
- 部分题目可能没有rating数据

## 许可证

MIT License
