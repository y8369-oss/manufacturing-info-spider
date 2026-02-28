# 制造业信息爬虫使用指南

## 📋 目录

- [快速开始](#快速开始)
- [GitHub Pages部署](#github-pages部署)
- [日常使用](#日常使用)
- [数据管理](#数据管理)
- [自动化更新](#自动化更新)
- [故障排查](#故障排查)

---

## 快速开始

### 1. 环境准备

确保已安装 Python 3.8+ 和必要的依赖：

```bash
cd C:\Users\qiuyi1\manufacturing_info_spider
pip install -r requirements.txt
```

### 2. 配置飞书机器人（可选）

如果需要推送到飞书群聊：

```bash
# Windows命令提示符
set FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-url
set FEISHU_SECRET=your-secret-key

# Windows PowerShell
$env:FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-url"
$env:FEISHU_SECRET="your-secret-key"
```

### 3. 测试运行

```bash
# 测试爬虫（不推送到飞书）
python main.py --type all --test

# 测试飞书连接
python main.py --test-feishu
```

---

## GitHub Pages部署

### 首次部署步骤

#### 1. 启用GitHub Pages

1. 访问GitHub仓库：https://github.com/y8369-oss/manufacturing-info-spider
2. 点击 **Settings** 标签
3. 在左侧菜单找到 **Pages**
4. 配置部署源：
   - **Source** > **Branch**: 选择 `main`
   - **Folder**: 选择 `/docs`
5. 点击 **Save** 保存

#### 2. 等待部署

- GitHub Actions会自动部署网站（约1-2分钟）
- 刷新页面后会显示部署状态
- 部署成功后会显示访问地址

#### 3. 访问网站

网站地址：**https://y8369-oss.github.io/manufacturing-info-spider/**

---

## 日常使用

### 数据抓取命令

```bash
# 1. 只抓取新闻
python main.py --type news

# 2. 只抓取论文和专利
python main.py --type papers_patents

# 3. 只更新网站（不抓取）
python main.py --type update_web

# 4. 执行所有任务（抓取+更新网站）
python main.py --type all
```

### 测试模式

```bash
# 测试模式：抓取少量数据，不推送到飞书
python main.py --type all --test

# 干运行模式：不保存数据，不推送（用于调试）
python main.py --type all --dry-run
```

### 完整的更新流程

每次更新数据并发布到网站：

```bash
# 1. 进入项目目录
cd C:\Users\qiuyi1\manufacturing_info_spider

# 2. 运行爬虫抓取所有数据
python main.py --type all

# 3. 复制网站文件到docs目录
cp -r output/website/* docs/

# 4. 提交到Git
git add docs/ output/
git commit -m "更新数据：$(date +%Y-%m-%d)"
git push origin main

# 等待1-2分钟，网站自动更新
```

### Windows批处理脚本

创建 `update_and_deploy.bat` 文件方便执行：

```batch
@echo off
echo ========================================
echo 制造业信息爬虫 - 数据更新与部署
echo ========================================

cd C:\Users\qiuyi1\manufacturing_info_spider

echo.
echo [1/4] 抓取数据...
python main.py --type all
if errorlevel 1 (
    echo 数据抓取失败！
    pause
    exit /b 1
)

echo.
echo [2/4] 复制网站文件...
xcopy /E /I /Y output\website\* docs\

echo.
echo [3/4] 提交到Git...
git add docs/ output/
git commit -m "更新数据：%date:~0,10%"

echo.
echo [4/4] 推送到GitHub...
git push origin main

echo.
echo ========================================
echo 更新完成！
echo 网站将在1-2分钟后自动更新
echo 访问地址：https://y8369-oss.github.io/manufacturing-info-spider/
echo ========================================
pause
```

使用方法：双击运行 `update_and_deploy.bat`

---

## 数据管理

### 清空数据库

```bash
# 使用专用脚本清空数据
python clear_database.py

# 或者删除数据库文件重新开始
rm data/crawler.db
```

### 配置数据源

#### 1. 修改关键词

编辑 `config/keywords.json`：

```json
{
  "news": {
    "robot": ["协作机器人", "人形机器人", "工业机器人"],
    "ai_tech": ["机器视觉", "深度学习", "大模型"]
  },
  "patents": ["机器人", "视觉", "传感器"],
  "papers": ["robotics", "manufacturing", "computer vision"]
}
```

#### 2. 添加/修改新闻源

编辑 `config/sources.json`：

```json
{
  "news_sources": [
    {
      "name": "网站名称",
      "base_url": "https://example.com",
      "search_url": "https://example.com/news/",
      "enabled": true,
      "type": "html"
    }
  ]
}
```

### 数据库查看

```bash
# 查看数据库统计
python -c "
import sqlite3
conn = sqlite3.connect('data/crawler.db')
cursor = conn.cursor()
news_count = cursor.execute('SELECT COUNT(*) FROM news').fetchone()[0]
patents_count = cursor.execute('SELECT COUNT(*) FROM patents').fetchone()[0]
papers_count = cursor.execute('SELECT COUNT(*) FROM papers').fetchone()[0]
print(f'新闻: {news_count}')
print(f'专利: {patents_count}')
print(f'论文: {papers_count}')
conn.close()
"
```

---

## 自动化更新

### 方案1：Windows任务计划程序

#### 创建定时任务

```bash
# 新闻抓取：每周一、三、五上午10:00
schtasks /create /tn "InfoSpider_News" /tr "python C:\Users\qiuyi1\manufacturing_info_spider\main.py --type news" /sc weekly /d MON,WED,FRI /st 10:00

# 论文+专利：每周五下午14:00
schtasks /create /tn "InfoSpider_Papers_Patents" /tr "python C:\Users\qiuyi1\manufacturing_info_spider\main.py --type papers_patents" /sc weekly /d FRI /st 14:00

# 网站更新与部署：每天晚上22:00
schtasks /create /tn "InfoSpider_Deploy" /tr "C:\Users\qiuyi1\manufacturing_info_spider\update_and_deploy.bat" /sc daily /st 22:00
```

#### 查看已创建的任务

```bash
schtasks /query /tn "InfoSpider_News"
schtasks /query /tn "InfoSpider_Papers_Patents"
schtasks /query /tn "InfoSpider_Deploy"
```

#### 删除任务

```bash
schtasks /delete /tn "InfoSpider_News" /f
schtasks /delete /tn "InfoSpider_Papers_Patents" /f
schtasks /delete /tn "InfoSpider_Deploy" /f
```

### 方案2：GitHub Actions自动部署

创建 `.github/workflows/update.yml`：

```yaml
name: 自动更新数据

on:
  schedule:
    # 每天UTC时间14:00（北京时间22:00）
    - cron: '0 14 * * *'
  workflow_dispatch: # 允许手动触发

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: 设置Python环境
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: 安装依赖
        run: pip install -r requirements.txt

      - name: 运行爬虫
        env:
          FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
          FEISHU_SECRET: ${{ secrets.FEISHU_SECRET }}
        run: python main.py --type all

      - name: 更新网站
        run: cp -r output/website/* docs/

      - name: 提交更改
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/ output/
          git commit -m "自动更新数据 $(date +'%Y-%m-%d %H:%M')" || exit 0
          git push
```

**注意**：需要在GitHub仓库的 Settings > Secrets 中添加 `FEISHU_WEBHOOK_URL` 和 `FEISHU_SECRET`。

---

## 故障排查

### 常见问题

#### 1. 爬虫失败 - 403/404错误

**原因**：网站反爬虫或URL失效

**解决方案**：
```bash
# 查看日志
cat spider.log | grep ERROR

# 临时禁用失败的源
# 编辑 config/sources.json，将 "enabled" 改为 false
```

#### 2. 飞书推送失败

**检查步骤**：
```bash
# 1. 测试飞书连接
python main.py --test-feishu

# 2. 验证环境变量
echo $FEISHU_WEBHOOK_URL
echo $FEISHU_SECRET

# 3. 检查日志
cat spider.log | grep feishu
```

#### 3. GitHub Pages未更新

**检查步骤**：
1. 确认文件已推送：`git log --oneline -n 5`
2. 查看GitHub Actions状态：https://github.com/y8369-oss/manufacturing-info-spider/actions
3. 清除浏览器缓存（Ctrl+F5强制刷新）
4. 等待3-5分钟再次检查

#### 4. 数据库损坏

```bash
# 备份并重建数据库
cp data/crawler.db data/crawler.db.backup
python clear_database.py
python main.py --type all
```

#### 5. 编码问题

如果在Windows中文环境下出现乱码：

```bash
# 设置环境变量
set PYTHONIOENCODING=utf-8

# 或在Python脚本开头添加
# -*- coding: utf-8 -*-
```

### 日志文件

查看详细日志：
```bash
# 查看最新50行日志
tail -n 50 spider.log

# 查看错误日志
grep ERROR spider.log

# 按时间过滤
grep "2026-02-28" spider.log
```

---

## 推荐工作流

### 每日维护（自动化）

- ✅ 自动抓取新数据
- ✅ 自动更新网站
- ✅ 自动推送到GitHub

### 每周检查（手动）

1. **周一**：检查数据质量和爬虫状态
   ```bash
   cat spider.log | grep -i error
   ```

2. **周三**：更新关键词配置（如需要）
   ```bash
   # 编辑 config/keywords.json
   ```

3. **周五**：检查网站访问情况
   - 访问：https://y8369-oss.github.io/manufacturing-info-spider/
   - 确认数据正常显示

### 每月优化（建议）

- 分析热门关键词，调整筛选策略
- 添加新的数据源
- 优化网站展示效果
- 清理过期数据（可选）

---

## 高级功能

### 1. 自定义筛选规则

编辑 `filters/keyword_filter.py` 调整筛选逻辑。

### 2. 修改推送频率

编辑 `config/settings.py`：

```python
NEWS_PER_WEEK = 3      # 每周推送新闻数量
PAPERS_PER_WEEK = 4    # 每周推送论文数量
PATENTS_PER_WEEK = 5   # 每周推送专利数量
```

### 3. 自定义网站样式

编辑 `web/templates/` 目录下的HTML模板文件。

### 4. 导出数据

```bash
# 导出为JSON
python -c "
import sqlite3, json
conn = sqlite3.connect('data/crawler.db')
cursor = conn.cursor()
news = cursor.execute('SELECT * FROM news').fetchall()
with open('export.json', 'w', encoding='utf-8') as f:
    json.dump([dict(zip(['id','title','url','source','date','summary','keywords','sent_date'], row)) for row in news], f, ensure_ascii=False, indent=2)
conn.close()
print('已导出到 export.json')
"
```

---

## 联系与支持

- **GitHub仓库**：https://github.com/y8369-oss/manufacturing-info-spider
- **问题反馈**：在GitHub上提交Issue
- **更新日志**：查看 Git commit history

---

## 附录：推荐配置

### 当前数据源

**新闻源**（8个）：
- 36氪
- 机器人网
- 智能制造网
- 雷锋网
- 盖世汽车社区
- 第一电动汽车网
- 赛雷
- 董车会

**论文源**（1个）：
- arXiv（涵盖cs.RO, cs.CV, cs.AI, cs.LG）

**专利源**（2个）：
- 国家知识产权局
- 百度学术专利

### 推荐扩展源

可以考虑添加：
- 机器之心
- 新智元
- 量子位
- IEEE Xplore
- Google Patents

---

**最后更新**：2026-02-28
**版本**：v1.0
