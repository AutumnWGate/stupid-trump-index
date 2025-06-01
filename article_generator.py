# article_generator.py
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from string import Template

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

class ArticleGenerator:
    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
        self.html_template = self.load_html_template()
        self.css_content = self.load_css_template()
        
    def load_html_template(self):
        """加载HTML模板"""
        template_path = self.template_dir / "article_template.html"
        
        # 如果模板文件不存在，创建默认模板
        if not template_path.exists():
            default_template = '''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>特朗普言论AI投资分析</title>
<style>
$css_content
</style>
</head>
<body>
<div class="container">
    <!-- 标题 -->
    <div class="header">
        <h1 class="title">特朗普最新言论AI投资分析</h1>
        <p class="subtitle">$subtitle</p>
    </div>
    
    <!-- 截图展示 -->
    <div class="screenshot-section">
        <img class="screenshot" src="$screenshot_url" alt="特朗普帖子截图">
        <p class="post-time">发布时间：$post_time</p>
    </div>
    
    <!-- 使用details/summary实现可折叠的标签页（微信兼容性更好） -->
    <div class="tabs-container">
        <details class="tab-panel" open>
            <summary>Gemini分析</summary>
            <div class="tab-panel-content">
                $gemini_content
            </div>
        </details>
        
        <details class="tab-panel">
            <summary>Grok分析</summary>
            <div class="tab-panel-content">
                $grok_content
            </div>
        </details>
        
        <details class="tab-panel">
            <summary>通义千问分析</summary>
            <div class="tab-panel-content">
                $qwen_content
            </div>
        </details>
    </div>
    
    <!-- 底部声明 -->
    <div class="disclaimer">
        <p>本分析由AI自动生成，仅供参考，不构成投资建议</p>
        <p>投资有风险，入市需谨慎</p>
        <p>更新时间：$update_time</p>
    </div>
</div>
</body>
</html>'''
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(default_template)
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return Template(f.read())
    
    def load_css_template(self):
        """加载CSS模板"""
        css_path = self.template_dir / "article_style.css"
        
        # 如果CSS文件不存在，创建默认样式
        if not css_path.exists():
            default_css = '''/* 基础样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: #f5f5f5;
    color: #333;
    line-height: 1.6;
}

.container {
    max-width: 750px;
    margin: 0 auto;
    background-color: #fff;
}

/* 标题区域 */
.header {
    padding: 20px 15px;
    text-align: center;
    background-color: #fff;
    border-bottom: 1px solid #e8e8e8;
}

.title {
    font-size: 20px;
    font-weight: bold;
    color: #000;
    margin-bottom: 10px;
}

.subtitle {
    font-size: 14px;
    color: #888;
}

/* 截图区域 */
.screenshot-section {
    padding: 20px 15px;
    text-align: center;
    background-color: #fafafa;
}

.screenshot {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.post-time {
    margin-top: 10px;
    font-size: 14px;
    color: #999;
}

/* 使用details/summary实现折叠效果 */
.tabs-container {
    margin-top: 20px;
}

.tab-panel {
    border-bottom: 1px solid #e8e8e8;
}

.tab-panel summary {
    padding: 15px;
    background-color: #f8f8f8;
    cursor: pointer;
    font-size: 16px;
    color: #333;
    font-weight: bold;
    list-style: none;
}

.tab-panel summary::-webkit-details-marker {
    display: none;
}

.tab-panel[open] summary {
    background-color: #07c160;
    color: #fff;
}

.tab-panel-content {
    padding: 20px 15px;
    min-height: 300px;
}

/* 分析内容样式 */
.score-section {
    text-align: center;
    padding: 20px;
    background-color: #f8f8f8;
    border-radius: 8px;
    margin-bottom: 20px;
}

.score-label {
    font-size: 14px;
    color: #666;
    margin-bottom: 10px;
}

.score-value {
    font-size: 48px;
    font-weight: bold;
    margin: 10px 0;
}

.score-positive {
    color: #07c160;
}

.score-negative {
    color: #fa5151;
}

.relevance {
    font-size: 14px;
    color: #999;
}

/* 分析卡片 */
.analysis-card {
    background-color: #f8f8f8;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 15px;
}

.analysis-card h3 {
    font-size: 16px;
    color: #333;
    margin-bottom: 10px;
}

.analysis-card p {
    margin-bottom: 8px;
    font-size: 14px;
    color: #666;
}

.analysis-card strong {
    color: #333;
}

/* 个股推荐卡片 */
.stock-card {
    background-color: #fff;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    margin-bottom: 10px;
}

.stock-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.stock-name {
    font-size: 16px;
    font-weight: bold;
    color: #333;
}

.stock-code {
    font-size: 14px;
    color: #999;
}

.stock-info {
    font-size: 14px;
    color: #666;
    margin-bottom: 10px;
}

.stock-logic {
    font-size: 14px;
    color: #666;
    margin-bottom: 10px;
    padding: 10px;
    background-color: #f8f8f8;
    border-radius: 4px;
}

.recommendation-tag {
    display: inline-block;
    padding: 6px 12px;
    background-color: #07c160;
    color: #fff;
    border-radius: 4px;
    font-size: 14px;
}

/* 风险提示 */
.risk-warning {
    background-color: #fff4e6;
    border: 1px solid #ffd591;
    padding: 15px;
    border-radius: 8px;
    margin-top: 20px;
}

.risk-warning h3 {
    color: #fa8c16;
    font-size: 16px;
    margin-bottom: 10px;
}

/* 底部声明 */
.disclaimer {
    padding: 30px 15px;
    text-align: center;
    font-size: 12px;
    color: #999;
    background-color: #fafafa;
    border-top: 1px solid #e8e8e8;
}

.disclaimer p {
    margin-bottom: 5px;
}'''
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(default_css)
        
        with open(css_path, 'r', encoding='utf-8') as f:
            return f.read()

    def generate_ai_content(self, ai_data, ai_name):
        """生成单个AI的分析内容"""
        if not ai_data or 'error' in ai_data:
            return f'<div style="text-align: center; padding: 50px; color: #999;">{ai_name}分析暂时不可用</div>'
        
        html = []
        
        # 综合评分
        score = ai_data.get('综合评分', '0%')
        score_class = 'score-positive' if '+' in score else 'score-negative'
        html.append(f'''
        <div class="score-section">
            <div class="score-label">综合评分</div>
            <div class="score-value {score_class}">{score}</div>
            <div class="relevance">市场相关性：{ai_data.get('市场相关性', '未知')}</div>
        </div>
        ''')
        
        # 影响分析
        if '影响分析' in ai_data:
            impact = ai_data['影响分析']
            html.append(f'''
            <div class="analysis-card">
                <h3>影响分析</h3>
                <p><strong>直接影响：</strong>{impact.get('直接影响', '无')}</p>
                <p><strong>影响路径：</strong>{impact.get('影响路径', '无')}</p>
                <p><strong>影响时限：</strong>{impact.get('影响时限', '无')}</p>
                <p><strong>影响强度：</strong>{impact.get('影响强度', '无')}</p>
            </div>
            ''')
        
        # 个股建议（最多显示5个）
        stocks = ai_data.get('个股建议', [])[:5]
        if stocks:
            html.append('<div class="analysis-card"><h3>个股建议</h3></div>')
            for stock in stocks:
                html.append(f'''
                <div class="stock-card">
                    <div class="stock-header">
                        <span class="stock-name">{stock.get('股票名称', '')}</span>
                        <span class="stock-code">{stock.get('股票代码', '')}</span>
                    </div>
                    <div class="stock-info">
                        {stock.get('所属行业', '')} | 目标价：{stock.get('目标价位', '')} | 预期收益：{stock.get('预期收益', '')}
                    </div>
                    <div class="stock-logic">
                        {stock.get('操作逻辑', '')}
                    </div>
                    <span class="recommendation-tag">{stock.get('交易建议', '')}</span>
                </div>
                ''')
        
        # 风险提示
        if '风险提示' in ai_data:
            html.append(f'''
            <div class="risk-warning">
                <h3>风险提示</h3>
                <p>{ai_data['风险提示']}</p>
            </div>
            ''')
        
        return ''.join(html)

    def generate_article(self, content_id):
        """生成完整的文章HTML"""
        # 读取分析数据
        summary_file = config.RESULT_DIR / f"{content_id}_all_ai_results.json"
        if not summary_file.exists():
            raise FileNotFoundError(f"分析结果文件不存在: {summary_file}")
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        post_data = data.get('post_data', {})
        ai_analysis = data.get('ai_analysis', {})
        
        # 准备截图URL（这里使用本地路径，实际发布时需要上传到微信）
        screenshot_path = config.SCREENSHOTS_DIR / f"{content_id}.png"
        
        # 生成各AI内容
        gemini_content = self.generate_ai_content(ai_analysis.get('gemini'), 'Gemini')
        grok_content = self.generate_ai_content(ai_analysis.get('grok'), 'Grok')
        qwen_content = self.generate_ai_content(ai_analysis.get('qwen'), '通义千问')
        
        # 读取模板
        template_path = self.template_dir / "article_template.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
        
        # 替换占位符
        html = html_template.replace('/* CSS_CONTENT_PLACEHOLDER */', self.css_content)
        html = html.replace('<!-- SUBTITLE_PLACEHOLDER -->', "三大AI深度解析对A股市场的影响")
        html = html.replace('<!-- SCREENSHOT_URL_PLACEHOLDER -->', f"cid:{content_id}.png")
        html = html.replace('<!-- POST_TIME_PLACEHOLDER -->', post_data.get('time', ''))
        html = html.replace('<!-- GEMINI_CONTENT_PLACEHOLDER -->', gemini_content)
        html = html.replace('<!-- GROK_CONTENT_PLACEHOLDER -->', grok_content)
        html = html.replace('<!-- QWEN_CONTENT_PLACEHOLDER -->', qwen_content)
        html = html.replace('<!-- UPDATE_TIME_PLACEHOLDER -->', datetime.now().strftime('%Y-%m-%d %H:%M'))
        
        # 保存HTML文件
        output_file = config.DATA_DIR / f"article_{content_id}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"文章已生成: {output_file}")
        return output_file, screenshot_path

if __name__ == "__main__":
    # 测试
    generator = ArticleGenerator()
    # 获取最新的content_id
    with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)
    if history:
        content_id = history[-1]['contentID']
        generator.generate_article(content_id)