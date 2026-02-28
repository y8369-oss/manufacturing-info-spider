# 制造业信息爬虫与飞书推送系统

自动化信息抓取系统，抓取制造业相关的新闻、专利、论文信息，通过关键词筛选后定时推送到飞书群聊，并生成静态网站供查看历史记录。
可通过网页查看：https://y8369-oss.github.io/manufacturing-info-spider/

## 功能特点

- 📰 **新闻爬取**: 从36氪、机器人网、智能制造网等网站抓取制造业新闻
- 🔬 **专利爬取**: 从国家知识产权局、百度学术抓取相关专利信息
- 📚 **论文爬取**: 从arXiv抓取机器人、制造业相关学术论文
- 🔍 **关键词筛选**: 基于关键词库智能过滤相关内容
- 🔄 **去重机制**: 基于SQLite数据库避免重复推送
- 📮 **飞书推送**: 通过飞书机器人推送精选内容到群聊
- 🌐 **静态网站**: 自动生成静态网站展示历史记录
- ⏰ **定时任务**: 支持Windows任务计划定时执行

## 推送频率

- **新闻**: 每周3条，不定时推送（周一、周三、周五）
- **论文+专利**: 每周五下午打包推送（论文4条+专利5条）

## 项目结构

```
manufacturing_info_spider/
├── config/                  # 配置文件
│   ├── keywords.json        # 关键词配置
│   ├── sources.json         # 信息源配置
│   └── settings.py          # 全局配置
├── crawlers/                # 爬虫模块
│   ├── base_crawler.py      # 爬虫基类
│   ├── news_crawler.py      # 新闻爬虫
│   ├── patent_crawler.py    # 专利爬虫
│   └── paper_crawler.py     # 论文爬虫
├── filters/                 # 筛选模块
│   ├── keyword_filter.py    # 关键词筛选
│   └── deduplication.py     # 去重逻辑
├── notifiers/               # 推送模块
│   └── feishu_bot.py        # 飞书机器人
├── database/                # 数据库模块
│   ├── models.py            # 数据模型
│   └── db_manager.py        # 数据库管理
├── web/                     # 网站生成
│   ├── templates/           # HTML模板
│   ├── static/              # 静态资源
│   └── generator.py         # 网站生成器
├── scheduler/               # 调度模块
│   └── task_scheduler.py    # 任务调度
├── data/                    # 数据目录
│   └── crawler.db           # SQLite数据库
├── output/                  # 输出目录
│   └── website/             # 静态网站
├── main.py                  # 主程序入口
├── requirements.txt         # 依赖清单
└── README.md                # 使用说明
```

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd manufacturing_info_spider
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

在系统环境变量或 `.env` 文件中配置飞书webhook：

```bash
# Windows (命令提示符)
set FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-url
set FEISHU_SECRET=your-secret-key

# Windows (PowerShell)
$env:FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-url"
$env:FEISHU_SECRET="your-secret-key"
```

## 使用方法

### 命令行参数

```bash
# 爬取新闻
python main.py --type news

# 爬取论文和专利
python main.py --type papers_patents

# 更新网站
python main.py --type update_web

# 执行所有任务
python main.py --type all

# 测试模式（爬取少量数据，不推送到飞书）
python main.py --type news --test

# 干运行模式（不保存数据，不推送）
python main.py --type news --dry-run

# 测试飞书机器人连接
python main.py --test-feishu

# 显示任务调度设置说明
python main.py --setup-scheduler
```

### 设置定时任务

#### 使用 schtasks 命令

```bash
# 新闻爬取：每周一、三、五上午10:00
schtasks /create /tn "InfoSpider_News" /tr "python C:\path\to\main.py --type news" /sc weekly /d MON,WED,FRI /st 10:00

# 论文+专利：每周五下午14:00
schtasks /create /tn "InfoSpider_Papers_Patents" /tr "python C:\path\to\main.py --type papers_patents" /sc weekly /d FRI /st 14:00

# 网站更新：每天晚上22:00
schtasks /create /tn "InfoSpider_WebUpdate" /tr "python C:\path\to\main.py --type update_web" /sc daily /st 22:00
```

#### 使用任务计划程序 GUI

1. 运行 `taskschd.msc` 打开任务计划程序
2. 创建任务 → 设置名称和描述
3. 触发器 → 新建 → 选择时间和频率
4. 操作 → 启动程序 → 选择 Python 和 main.py
5. 保存任务

## 配置说明

### keywords.json

配置用于筛选内容的关键词：

```json
{
  "news": {
    "robot": ["协作机器人", "工业机器人", "AGV"],
    "ai_tech": ["视觉检测", "机器视觉", "深度学习"],
    "smart_manufacturing": ["智能工厂", "数字孪生"]
  },
  "patents": ["机器人", "协作", "视觉", "传感器"],
  "papers": ["robotics", "manufacturing", "computer vision"]
}
```

### sources.json

配置信息来源：

```json
{
  "news_sources": [
    {
      "name": "36氪",
      "base_url": "https://www.36kr.com",
      "enabled": true
    }
  ],
  "patent_sources": [...],
  "paper_sources": [...]
}
```

### settings.py

配置全局参数、飞书设置、爬虫参数等。

## 数据库

使用 SQLite 存储数据，包含三个主要表：

- `news`: 新闻文章
- `patents`: 专利信息
- `papers`: 学术论文

每条记录包含：标题、链接、来源、日期、摘要、关键词、推送状态等。

## 静态网站

生成的静态网站包含：

- 首页：最新内容概览
- 新闻页：所有新闻列表
- 专利页：所有专利列表
- 论文页：所有论文列表

支持前端搜索和关键词筛选。

## 注意事项

### 反爬虫策略

- 添加随机延迟（1-3秒）
- 轮换 User-Agent
- 遵守 robots.txt
- 请求失败自动重试（最多3次）

### 数据安全

- 飞书 webhook URL 存储在环境变量中
- 不在代码中硬编码敏感信息
- 不在公开仓库中提交配置文件

### 合规性

- 遵守网站使用条款
- 尊重版权
- 仅用于个人学习和研究

## 故障排查

### 爬虫失败

- 检查网络连接
- 查看日志文件 `spider.log`
- 验证信息源是否可访问
- 确认关键词配置正确

### 飞书推送失败

- 验证 webhook URL 是否正确
- 检查飞书机器人是否已添加到群聊
- 查看错误日志
- 运行 `python main.py --test-feishu` 测试连接

### 数据库问题

- 确认 `data/` 目录存在
- 检查数据库文件权限
- 清空数据库：删除 `data/crawler.db` 文件

## 日志

日志文件位于项目根目录的 `spider.log`，记录：

- 爬虫执行情况
- 数据筛选结果
- 推送状态
- 错误信息

## 开发

### 添加新的信息源

1. 在 `sources.json` 中添加源配置
2. 在对应的爬虫模块中实现解析逻辑
3. 测试爬取效果

### 自定义关键词

编辑 `config/keywords.json`，添加或修改关键词类别。

### 修改推送格式

编辑 `notifiers/feishu_bot.py` 中的卡片生成方法。

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。

---

**Powered by Manufacturing Info Spider** 🤖
