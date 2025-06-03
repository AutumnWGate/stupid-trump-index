# article_generator.py
import os
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config

class ArticleGenerator:
    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
    def load_template(self, filename):
        """加载模板文件"""
        template_path = self.template_dir / filename
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def generate_score_table(self, ai_analysis):
        """生成评分对比表格（内联样式）"""
        rows = []
        
        # 表格样式
        table_style = "width:100%;border-collapse:collapse;margin:20px 0;font-size:14px;"
        th_style = "padding:10px;text-align:left;border:1px solid #e8e8e8;background-color:#f8f8f8;font-weight:bold;"
        td_style = "padding:10px;text-align:left;border:1px solid #e8e8e8;background-color:#fff;"
        
        # Gemini
        gemini_data = ai_analysis.get('gemini', {})
        gemini_score = gemini_data.get('综合评分', '暂无')
        score_color = '#07c160' if '+' in str(gemini_score) else '#fa5151'
        rows.append(f'''
            <tr>
                <td style="{td_style}"><strong>Gemini</strong></td>
                <td style="{td_style}color:{score_color};font-weight:bold;font-size:16px;">{gemini_score}</td>
                <td style="{td_style}">{gemini_data.get('市场相关性', '未知')}</td>
            </tr>
        ''')
        
        # Grok
        grok_data = ai_analysis.get('grok', {})
        grok_score = grok_data.get('综合评分', '暂无')
        score_color = '#07c160' if '+' in str(grok_score) else '#fa5151'
        rows.append(f'''
            <tr>
                <td style="{td_style}"><strong>Grok</strong></td>
                <td style="{td_style}color:{score_color};font-weight:bold;font-size:16px;">{grok_score}</td>
                <td style="{td_style}">{grok_data.get('市场相关性', '未知')}</td>
            </tr>
        ''')
        
        # 通义千问
        qwen_data = ai_analysis.get('qwen', {})
        qwen_score = qwen_data.get('综合评分', '暂无')
        score_color = '#07c160' if '+' in str(qwen_score) else '#fa5151'
        rows.append(f'''
            <tr>
                <td style="{td_style}"><strong>通义千问</strong></td>
                <td style="{td_style}color:{score_color};font-weight:bold;font-size:16px;">{qwen_score}</td>
                <td style="{td_style}">{qwen_data.get('市场相关性', '未知')}</td>
            </tr>
        ''')
        
        return f'''
        <table style="{table_style}">
            <thead>
                <tr>
                    <th style="{th_style}">AI模型</th>
                    <th style="{th_style}">综合评分</th>
                    <th style="{th_style}">市场相关性</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        '''
    
    def generate_impact_table(self, ai_analysis):
        """生成影响分析对比表格（内联样式）"""
        # 表格样式
        table_style = "width:100%;border-collapse:collapse;margin:20px 0;font-size:14px;"
        th_style = "padding:10px;text-align:left;border:1px solid #e8e8e8;background-color:#f8f8f8;font-weight:bold;"
        td_style = "padding:10px;text-align:left;border:1px solid #e8e8e8;background-color:#fff;font-size:13px;"
        
        # 获取各AI的影响分析数据
        gemini_impact = ai_analysis.get('gemini', {}).get('影响分析', {})
        grok_impact = ai_analysis.get('grok', {}).get('影响分析', {})
        qwen_impact = ai_analysis.get('qwen', {}).get('影响分析', {})
        
        rows = []
        
        # 直接影响
        rows.append(f'''
            <tr>
                <td style="{th_style}">直接影响</td>
                <td style="{td_style}">{gemini_impact.get('直接影响', '暂无分析')}</td>
                <td style="{td_style}">{grok_impact.get('直接影响', '暂无分析')}</td>
                <td style="{td_style}">{qwen_impact.get('直接影响', '暂无分析')}</td>
            </tr>
        ''')
        
        # 影响路径
        rows.append(f'''
            <tr>
                <td style="{th_style}">影响路径</td>
                <td style="{td_style}">{gemini_impact.get('影响路径', '暂无分析')}</td>
                <td style="{td_style}">{grok_impact.get('影响路径', '暂无分析')}</td>
                <td style="{td_style}">{qwen_impact.get('影响路径', '暂无分析')}</td>
            </tr>
        ''')
        
        # 影响时限
        rows.append(f'''
            <tr>
                <td style="{th_style}">影响时限</td>
                <td style="{td_style}">{gemini_impact.get('影响时限', '暂无分析')}</td>
                <td style="{td_style}">{grok_impact.get('影响时限', '暂无分析')}</td>
                <td style="{td_style}">{qwen_impact.get('影响时限', '暂无分析')}</td>
            </tr>
        ''')
        
        # 影响强度
        rows.append(f'''
            <tr>
                <td style="{th_style}">影响强度</td>
                <td style="{td_style}">{gemini_impact.get('影响强度', '暂无分析')}</td>
                <td style="{td_style}">{grok_impact.get('影响强度', '暂无分析')}</td>
                <td style="{td_style}">{qwen_impact.get('影响强度', '暂无分析')}</td>
            </tr>
        ''')
        
        return f'''
        <table style="{table_style}">
            <thead>
                <tr>
                    <th style="{th_style}">分析维度</th>
                    <th style="{th_style}">Gemini</th>
                    <th style="{th_style}">Grok</th>
                    <th style="{th_style}">通义千问</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        '''
    
    def generate_stocks_content(self, ai_analysis):
        """生成个股建议汇总（内联样式）"""
        html = []
        
        # 容器样式
        container_style = "background-color:#f8f8f8;padding:15px;border-radius:8px;margin-bottom:20px;"
        group_style = "margin-bottom:15px;padding-bottom:15px;border-bottom:1px solid #e8e8e8;"
        ai_name_style = "font-size:15px;font-weight:bold;color:#333;margin-bottom:10px;"
        stock_item_style = "background-color:#fff;padding:10px;margin-bottom:8px;border-radius:4px;border:1px solid #e8e8e8;"
        stock_name_style = "font-size:14px;font-weight:bold;color:#333;"
        stock_code_style = "font-size:12px;color:#666;"
        stock_info_style = "font-size:12px;color:#666;margin-top:5px;"
        tag_style = "display:inline-block;padding:2px 8px;background-color:#07c160;color:#fff;border-radius:2px;font-size:12px;"
        no_rec_style = "font-size:13px;color:#999;font-style:italic;"
        
        html.append(f'<div style="{container_style}">')
        
        # 处理每个AI的个股建议
        ai_list = [('gemini', 'Gemini'), ('grok', 'Grok'), ('qwen', '通义千问')]
        for i, (ai_name, ai_label) in enumerate(ai_list):
            ai_data = ai_analysis.get(ai_name, {})
            stocks = ai_data.get('个股建议', [])[:3]  # 每个AI最多显示3个股票
            
            # 最后一个不需要底部边框
            current_group_style = group_style if i < len(ai_list) - 1 else "margin-bottom:0;"
            
            html.append(f'<div style="{current_group_style}">')
            html.append(f'<div style="{ai_name_style}">{ai_label}</div>')
            
            if stocks:
                for stock in stocks:
                    html.append(f'''
                    <div style="{stock_item_style}">
                        <div>
                            <span style="{stock_name_style}">{stock.get('股票名称', '')}</span>
                            <span style="{stock_code_style}"> {stock.get('股票代码', '')}</span>
                            <span style="{tag_style};float:right;">{stock.get('交易建议', '')}</span>
                        </div>
                        <div style="{stock_info_style}">
                            {stock.get('所属行业', '')} | 目标价：{stock.get('目标价位', '')} | 预期收益：{stock.get('预期收益', '')}
                        </div>
                        <div style="{stock_info_style}">
                            {stock.get('操作逻辑', '')}
                        </div>
                    </div>
                    ''')
            else:
                html.append(f'<div style="{no_rec_style}">暂无个股建议</div>')
            
            html.append('</div>')
        
        html.append('</div>')
        return ''.join(html)
    
    def generate_risk_content(self, ai_analysis):
        """生成风险提示汇总（内联样式）"""
        html = []
        
        # 容器样式
        container_style = "background-color:#fff4e6;border:1px solid #ffd591;padding:15px;border-radius:8px;"
        item_style = "margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid #ffd591;"
        ai_name_style = "font-size:14px;font-weight:bold;color:#fa8c16;margin-bottom:5px;"
        content_style = "font-size:13px;color:#666;"
        
        html.append(f'<div style="{container_style}">')
        
        # 处理每个AI的风险提示
        risk_items = []
        for ai_name, ai_label in [('gemini', 'Gemini'), ('grok', 'Grok'), ('qwen', '通义千问')]:
            ai_data = ai_analysis.get(ai_name, {})
            risk_warning = ai_data.get('风险提示', '')
            
            if risk_warning:
                risk_items.append((ai_label, risk_warning))
        
        if risk_items:
            for i, (ai_label, risk_warning) in enumerate(risk_items):
                # 最后一个不需要底部边框
                current_item_style = item_style if i < len(risk_items) - 1 else ""
                html.append(f'''
                <div style="{current_item_style}">
                    <div style="{ai_name_style}">{ai_label}</div>
                    <div style="{content_style}">{risk_warning}</div>
                </div>
                ''')
        else:
            html.append(f'<div style="{content_style}">暂无风险提示</div>')
        
        html.append('</div>')
        return ''.join(html)

    def generate_article(self, content_id):
        """生成完整的文章HTML（符合微信公众号要求）"""
        # 读取分析数据
        summary_file = config.RESULT_DIR / f"{content_id}_all_ai_results.json"
        if not summary_file.exists():
            raise FileNotFoundError(f"分析结果文件不存在: {summary_file}")
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        post_data = data.get('post_data', {})
        ai_analysis = data.get('ai_analysis', {})
        
        # 加载模板
        html_template = self.load_template('article_template.html')
        
        if not html_template:
            raise FileNotFoundError("模板文件不存在")
        
        # 生成各部分内容
        score_table_content = self.generate_score_table(ai_analysis)
        impact_table_content = self.generate_impact_table(ai_analysis)
        stocks_content = self.generate_stocks_content(ai_analysis)
        risk_content = self.generate_risk_content(ai_analysis)
        
        # 替换占位符
        html = html_template
        html = html.replace('<!-- SUBTITLE_PLACEHOLDER -->', "三大AI深度解析对A股市场的影响")
        html = html.replace('<!-- SCREENSHOT_URL_PLACEHOLDER -->', f"cid:{content_id}.png")
        html = html.replace('<!-- POST_TIME_PLACEHOLDER -->', post_data.get('time', ''))
        html = html.replace('<!-- SCORE_TABLE_CONTENT -->', score_table_content)
        html = html.replace('<!-- IMPACT_TABLE_CONTENT -->', impact_table_content)
        html = html.replace('<!-- STOCKS_CONTENT -->', stocks_content)
        html = html.replace('<!-- RISK_CONTENT -->', risk_content)
        html = html.replace('<!-- UPDATE_TIME_PLACEHOLDER -->', datetime.now().strftime('%Y-%m-%d %H:%M'))
        
        # 保存HTML文件
        output_file = config.DATA_DIR / f"article_{content_id}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"文章已生成: {output_file}")
        
        # 返回文件路径和截图路径
        screenshot_path = config.SCREENSHOTS_DIR / f"{content_id}.png"
        return output_file, screenshot_path

if __name__ == "__main__":
    # 测试数据保持不变
    test_data = {
        "post_data": {
            "time": "2024-01-15 10:30"
        },
        "ai_analysis": {
            "gemini": {
                "综合评分": "+15%",
                "市场相关性": "高度相关",
                "影响分析": {
                    "直接影响": "特朗普政策对科技行业利好",
                    "影响路径": "政策 → 科技股 → 整体市场",
                    "影响时限": "短期(1-3个月)",
                    "影响强度": "中等"
                },
                "个股建议": [
                    {
                        "股票名称": "腾讯控股",
                        "股票代码": "00700.HK",
                        "所属行业": "互联网",
                        "目标价位": "450港元",
                        "预期收益": "+20%",
                        "交易建议": "买入",
                        "操作逻辑": "受益于政策放松"
                    }
                ],
                "风险提示": "需关注政策变化风险"
            },
            "grok": {
                "综合评分": "-10%",
                "市场相关性": "中度相关",
                "影响分析": {
                    "直接影响": "短期波动加大",
                    "影响路径": "言论 → 市场情绪 → 股价",
                    "影响时限": "短期(1周内)",
                    "影响强度": "较弱"
                },
                "风险提示": "市场情绪波动风险"
            },
            "qwen": {
                "综合评分": "+5%",
                "市场相关性": "低度相关",
                "影响分析": {
                    "直接影响": "间接影响A股市场",
                    "影响路径": "美股 → 港股 → A股",
                    "影响时限": "中期(3-6个月)",
                    "影响强度": "较弱"
                },
                "个股建议": [
                    {
                        "股票名称": "比亚迪",
                        "股票代码": "002594.SZ",
                        "所属行业": "新能源汽车",
                        "目标价位": "280元",
                        "预期收益": "+15%",
                        "交易建议": "增持",
                        "操作逻辑": "新能源政策受益"
                    }
                ],
                "风险提示": "汇率波动风险"
            }
        }
    }
    
    # 保存测试数据
    test_content_id = "114606254307800195"
    test_file = config.RESULT_DIR / f"{test_content_id}_all_ai_results.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    # 生成文章
    generator = ArticleGenerator()
    generator.generate_article(test_content_id)