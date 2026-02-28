# 飞书机器人配置指南

## 📱 什么是飞书机器人

飞书机器人可以自动将爬取的制造业信息推送到飞书群聊，实现信息的自动分发和团队协作。

---

## 🚀 快速配置（5分钟）

### 第一步：创建飞书机器人

#### 1. 打开飞书群聊

- 打开您想要接收信息的飞书群聊
- 点击右上角 **···** (更多选项)

#### 2. 添加自定义机器人

1. 选择 **设置** → **群机器人** → **添加机器人**
2. 选择 **自定义机器人**
3. 配置机器人信息：
   - **名称**：制造业信息爬虫
   - **描述**：自动推送制造业新闻、论文、专利
   - **头像**：可选择机器人图标

#### 3. 获取Webhook地址

1. 点击 **添加** 后，会显示 **Webhook地址**
2. 复制这个地址（形如：`https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxx`）
3. **重要**：同时记录下 **签名密钥**（Secret）

示例：
```
Webhook地址：https://open.feishu.cn/open-apis/bot/v2/hook/abc123def456
签名密钥：SECxxxxxxxxxxxxxxxxxxxxx
```

---

### 第二步：配置环境变量

#### Windows 命令提示符

打开CMD，执行：

```batch
# 设置Webhook URL
setx FEISHU_WEBHOOK_URL "https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook地址"

# 设置签名密钥
setx FEISHU_SECRET "你的签名密钥"
```

**注意**：设置后需要重启命令提示符或PowerShell才能生效。

#### Windows PowerShell

打开PowerShell，执行：

```powershell
# 设置Webhook URL
[System.Environment]::SetEnvironmentVariable('FEISHU_WEBHOOK_URL', 'https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook地址', 'User')

# 设置签名密钥
[System.Environment]::SetEnvironmentVariable('FEISHU_SECRET', '你的签名密钥', 'User')
```

**注意**：设置后需要重启PowerShell才能生效。

#### 临时设置（单次会话）

如果只是测试，可以临时设置：

```batch
# CMD
set FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook地址
set FEISHU_SECRET=你的签名密钥

# PowerShell
$env:FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook地址"
$env:FEISHU_SECRET="你的签名密钥"
```

---

### 第三步：验证配置

#### 1. 测试连接

```bash
cd C:\Users\qiuyi1\manufacturing_info_spider
python main.py --test-feishu
```

**成功提示**：
```
Feishu bot test successful!
```

您应该在飞书群聊中看到测试消息：
> 🤖 Manufacturing Info Spider 测试消息

#### 2. 测试数据推送

```bash
# 测试模式：抓取少量数据并推送
python main.py --type news --test
```

---

## 📊 推送内容说明

### 新闻推送

- **推送频率**：每周3条
- **推送时间**：不定时（周一、三、五）
- **内容格式**：
  - 标题
  - 摘要
  - 来源
  - 发布时间
  - 关键词标签
  - 原文链接

### 论文+专利推送

- **推送频率**：每周一次
- **推送时间**：周五下午
- **内容格式**：
  - 论文4篇 + 专利5项
  - 打包在一张卡片中
  - 包含标题、作者、摘要、链接

---

## 🔧 高级配置

### 修改推送数量

编辑 `config/settings.py`：

```python
# 每周推送数量配置
NEWS_PER_WEEK = 3      # 新闻每周3条
PAPERS_PER_WEEK = 4    # 论文每周4篇
PATENTS_PER_WEEK = 5   # 专利每周5项
```

修改后重新运行即可生效。

### 自定义推送格式

编辑 `notifiers/feishu_bot.py`，修改以下方法：

- `send_news_batch()` - 新闻推送格式
- `send_papers_and_patents()` - 论文专利推送格式

### 添加错误通知

系统已自动配置错误通知，当爬虫出错时会自动发送告警消息到飞书群。

---

## 🔐 安全建议

### 1. 保护Webhook地址

- ❌ **不要**将Webhook地址提交到公开的Git仓库
- ✅ **使用**环境变量存储敏感信息
- ✅ **定期**更换签名密钥

### 2. 使用.env文件（推荐）

创建 `.env` 文件（已在.gitignore中）：

```bash
# .env
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/你的webhook地址
FEISHU_SECRET=你的签名密钥
```

安装python-dotenv：

```bash
pip install python-dotenv
```

在 `config/settings.py` 中添加：

```python
from dotenv import load_dotenv
load_dotenv()
```

这样可以自动加载.env文件中的配置。

---

## 🎯 使用场景

### 场景1：个人学习

```bash
# 每天晚上运行，第二天早上看到最新信息
python main.py --type all
```

### 场景2：团队协作

- 设置自动定时任务（见USAGE_GUIDE.md）
- 团队成员在飞书群中接收信息
- 可以直接在群内讨论和分享

### 场景3：仅网站展示，不推送飞书

不配置环境变量，直接运行：

```bash
python main.py --type all
```

系统会自动跳过飞书推送，只更新网站。

---

## ❓ 故障排查

### 问题1：提示"Feishu webhook URL not configured"

**原因**：未配置环境变量

**解决方案**：
```bash
# 检查环境变量
echo %FEISHU_WEBHOOK_URL%  # CMD
echo $env:FEISHU_WEBHOOK_URL  # PowerShell

# 如果为空，重新设置环境变量并重启终端
```

### 问题2：推送失败，返回错误

**可能原因**：
1. Webhook地址错误
2. 签名密钥不匹配
3. 机器人被移除群聊
4. 网络连接问题

**解决方案**：
```bash
# 1. 测试连接
python main.py --test-feishu

# 2. 检查日志
cat spider.log | grep feishu

# 3. 重新获取Webhook地址和密钥
# 在飞书群中：设置 → 群机器人 → 查看现有机器人
```

### 问题3：收不到消息

**检查清单**：
- [ ] 机器人是否还在群聊中
- [ ] Webhook地址是否正确
- [ ] 程序是否成功运行（检查日志）
- [ ] 数据是否被标记为"已发送"

```bash
# 查看数据库中的发送状态
python -c "
import sqlite3
conn = sqlite3.connect('data/crawler.db')
cursor = conn.cursor()
unsent = cursor.execute('SELECT COUNT(*) FROM news WHERE sent_date IS NULL').fetchone()[0]
print(f'未发送的新闻：{unsent}条')
conn.close()
"
```

### 问题4：重复推送

**原因**：数据库中的sent_date字段未正确更新

**解决方案**：
```bash
# 手动标记所有数据为已发送
python -c "
import sqlite3
from datetime import datetime
conn = sqlite3.connect('data/crawler.db')
cursor = conn.cursor()
now = datetime.now().isoformat()
cursor.execute('UPDATE news SET sent_date = ? WHERE sent_date IS NULL', (now,))
cursor.execute('UPDATE papers SET sent_date = ? WHERE sent_date IS NULL', (now,))
cursor.execute('UPDATE patents SET sent_date = ? WHERE sent_date IS NULL', (now,))
conn.commit()
conn.close()
print('已标记所有数据为已发送')
"
```

---

## 📱 飞书机器人管理

### 查看机器人信息

1. 打开飞书群聊
2. 设置 → 群机器人
3. 点击已添加的机器人查看详情

### 修改机器人配置

1. 点击机器人 → 设置
2. 可以修改名称、描述、头像
3. **重要**：重新生成Webhook会导致旧地址失效

### 删除机器人

1. 设置 → 群机器人
2. 点击机器人 → 删除
3. 删除后需要重新配置

### 临时禁用推送

不想删除机器人，只是临时不推送：

```bash
# 使用test模式（不推送到飞书）
python main.py --type all --test

# 或者临时清空环境变量
set FEISHU_WEBHOOK_URL=
```

---

## 🔄 完整工作流程

### 一次性配置（首次使用）

1. ✅ 创建飞书机器人，获取Webhook和密钥
2. ✅ 配置环境变量
3. ✅ 测试连接：`python main.py --test-feishu`
4. ✅ 测试推送：`python main.py --type news --test`

### 日常使用（自动化）

```bash
# 方式1：手动运行
python main.py --type all

# 方式2：Windows定时任务
schtasks /create /tn "InfoSpider_Daily" /tr "python C:\Users\qiuyi1\manufacturing_info_spider\main.py --type all" /sc daily /st 22:00

# 方式3：批处理脚本（推荐）
# 双击运行 update_and_deploy.bat
```

### 推送逻辑

```
运行爬虫
  ↓
抓取数据
  ↓
关键词筛选
  ↓
去重检查
  ↓
保存到数据库
  ↓
读取未发送数据（sent_date为NULL）
  ↓
发送到飞书（TOP N条）
  ↓
标记为已发送（更新sent_date）
  ↓
更新网站
```

---

## 📚 参考资料

- [飞书开放平台 - 自定义机器人](https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN)
- [飞书机器人消息卡片设计](https://open.feishu.cn/document/ukTMukTMukTM/uEjNwUjLxYDM14SM2ATN)
- 项目代码：`notifiers/feishu_bot.py`

---

## 💡 使用建议

1. **首次配置**：先使用test模式确认推送正常
2. **团队使用**：建议在专门的信息群中使用
3. **推送频率**：根据团队需求调整推送数量
4. **数据质量**：定期检查推送内容的相关性，调整关键词
5. **备份配置**：将Webhook地址记录在安全的地方

---

## 🎉 配置成功标志

当您看到以下内容时，说明配置成功：

1. ✅ `python main.py --test-feishu` 显示成功
2. ✅ 飞书群中收到测试消息
3. ✅ `python main.py --type news --test` 后收到新闻推送
4. ✅ 日志中显示 "Sent X news to Feishu"

---

**祝您使用愉快！** 🚀

如有问题，请查看日志文件 `spider.log` 或提交GitHub Issue。
