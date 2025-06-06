# 🎺 川建国A股指数预测器 (Stupid Trump Index) 

> 🎯 **项目创意来源**：BigCoke  
> 👨‍💻 **开发者**：AutumnWestGate

## 🤔 这是个什么鬼？

欢迎来到史上最离谱的A股分析工具！🎉

本项目通过实时监控川建国同志（Donald Trump）在Truth Social上的最新发言，运用三大顶级AI（通义千问、Grok、Gemini）进行深度分析，预测其对A股市场的影响，并自动发布到微信公众号。

**友情提醒**：如果你真的根据川普的推文来炒股，那你可能需要的不是这个工具，而是一个心理医生。😅

## 🎨 项目架构图

```mermaid
graph TD
    A[🎺 Truth Social] -->|爬虫采集| B[📸 内容采集器]
    B --> C[📊 三大AI分析引擎]
    
    C --> D[🤖 通义千问]
    C --> E[🧠 Grok]  
    C --> F[✨ Gemini]
    
    D --> G[📝 文章生成器]
    E --> G
    F --> G
    
    G --> H[📱 微信公众号发布器]
    H --> I[🎉 粉丝们的快乐源泉]
    
    style A fill:#ff6b6b
    style I fill:#4ecdc4
```

## 🚀 部署指南

### 1. 环境要求

- Python 3.8+
- Chrome/Chromium 浏览器
- 稳定的网络连接（你懂的，需要科学上网 🪜）

### 2. 安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/stupid_trump_index.git
cd stupid_trump_index

# 安装依赖
pip install -r requirements.txt

# 如果使用 undetected-chromedriver
pip install undetected-chromedriver selenium
```

### 3. 配置环境变量

创建 `.env` 文件，填入你的API密钥：

```env
# AI服务密钥
DASHSCOPE_API_KEY=your_qwen_key        # 通义千问
XAI_API_KEY=your_grok_key              # Grok  
GEMINI_API_KEY=your_gemini_key         # Gemini

# 微信公众号配置
WECHAT_APPID=your_appid
WECHAT_APPSECRET=your_appsecret

# 可选：使用 undetected-chromedriver
USE_UNDETECTED_CHROME=true
```

### 4. 配置代理（如需要）

修改 `scraper.py` 中的代理设置：

```python
proxy={"server": "socks5://127.0.0.1:10808"}  # 改成你的代理
```

## 🎮 使用方法

### 基础用法

```bash
# 单次运行（采集→分析→生成→发布）
python main.py --once

# 持续监控（每30分钟检查一次）
python main.py --interval 30

# 只采集分析，不发布
python main.py --once --skip-publish

# 采集第3个非置顶帖子
python main.py --once --post-index 2
```

### 高级玩法

1. **定时任务**：使用 cron 或 Windows 任务计划程序
2. **Docker部署**：确保容器内有Chrome环境
3. **云服务器部署**：推荐使用有GUI的VPS，方便调试

## 📊 AI分析维度

每个AI都会从以下角度分析川普的言论：

- 🎯 **综合评分**：预测对A股的影响（+15% ~ -20%）
- 🌍 **市场相关性**：高/中/低
- 📈 **影响分析**：
  - 直接影响
  - 影响路径
  - 影响时限
  - 影响强度
- 💎 **个股建议**：具体股票推荐（如果有）
- ⚠️ **风险提示**：友情提醒别当真

## 🎪 项目特色

1. **三个臭皮匠顶个诸葛亮**：三大AI同时分析，结果更"可靠"（咳咳）
2. **自动截图**：完美保存川普的"智慧结晶"
3. **一键发布**：自动生成文章并发布到公众号
4. **反爬虫对抗**：使用 undetected-chromedriver，让Truth Social以为是真人在访问

## ⚠️ 免责声明

### 🎭 娱乐声明

1. **本项目纯属娱乐**，如有雷同，纯属巧合
2. **请勿当真**！川普的推文和A股的关系，可能还不如你家猫的心情和明天天气的关系
3. **投资有风险**，跟着川普炒股需谨慎（其实是千万别信）
4. **本项目不对任何投资损失负责**，包括但不限于：
   - 因为相信AI分析而亏钱
   - 因为川普突然发疯而导致的市场波动
   - 因为笑得太厉害而按错交易按钮

### 📜 法律声明

1. 本项目仅供学习和研究使用
2. 请遵守相关法律法规，不要用于商业用途
3. 爬虫使用请遵守robots协议（虽然Truth Social可能没有）
4. 微信公众号发布请遵守相关规定

## 🤝 贡献指南

欢迎提交PR！特别是：

- 🐛 修复bug（肯定有不少）
- 🎨 改进UI（虽然是后端项目）
- 😂 增加更多幽默元素
- 🧠 接入更多AI（比如ChatGPT也来凑个热闹）

## 📄 开源协议

本项目采用 MIT 协议，简单说就是：
- ✅ 你可以随便用
- ✅ 你可以随便改
- ✅ 你可以随便分发
- ❌ 但是出了问题别找我

## 🎬 结语

记住，股市有风险，川普更有风险。本项目的存在只是为了证明：

> "在这个魔幻的时代，用AI分析川普推文来预测A股，可能是最不魔幻的事情了。"

**最后的最后**：如果这个项目真的帮你赚到了钱，请记得：
1. 这纯属运气
2. 快去买彩票
3. 记得请开发者喝咖啡 ☕

---

*本README最后更新于2025年，那时川普可能又在搞什么新花样了...*

🌟 **觉得好玩？给个Star吧！** 🌟
