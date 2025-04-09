import pandas as pd
import requests
import json
import time
import os
import argparse
from tqdm import tqdm

def call_deepseek_api(api_key, input_text, max_tokens=2048):
    """调用DeepSeek API进行文本分析"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",  # 或其他适用的DeepSeek模型
        "messages": [
            {
                "role": "system", 
                "content": """你是一个学术论文分析助手。你需要完成两个任务：
                1. 用一句话概述论文的主要内容和贡献
                2. 用一句话分析论文与以下研究方向的相关性：音频预训练模型过程中音频片段最优长度和训练数据高效筛选
                   (关键词：自监督、预训练、scaling、数据筛选、信息瓶颈)
                
                请按以下格式输出：
                概述：[一句话论文概述]
                相关性：[一句话相关性分析，包含相关性程度（高/中/低）和具体原因]
                """
            },
            {
                "role": "user",
                "content": input_text
            }
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1  # 低温度使输出更确定性
    }
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",  # 请根据实际API端点调整
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"API调用出错: {e}")
        return f"分析失败: {str(e)}"

def analyze_paper(api_key, title, abstract, authors=None):
    """分析单篇论文，生成概述和相关性评估"""
    # 构建输入文本
    input_text = f"论文标题: {title}\n\n"
    if authors:
        input_text += f"作者: {authors}\n\n"
    input_text += f"摘要: {abstract}\n\n"
    input_text += "请分析这篇论文的主要内容和它与音频预训练模型、数据筛选相关研究的相关性。"
    
    # 调用API
    result = call_deepseek_api(api_key, input_text)
    
    # 解析结果
    try:
        # 提取概述和相关性评估
        overview = ""
        relevance = ""
        
        if "概述：" in result and "相关性：" in result:
            # 按格式分离
            parts = result.split("相关性：")
            overview_part = parts[0].strip()
            relevance = parts[1].strip()
            
            if "概述：" in overview_part:
                overview = overview_part.split("概述：")[1].strip()
            else:
                overview = overview_part
        else:
            # 如果格式不一致，尝试识别前两段
            paragraphs = [p.strip() for p in result.split('\n') if p.strip()]
            if len(paragraphs) >= 1:
                overview = paragraphs[0]
            if len(paragraphs) >= 2:
                relevance = paragraphs[1]
        
        print(f"paper:{title},overview:{overview},relevance:{relevance}")
        return {
            "overview": overview,
            "relevance": relevance
        }
    except Exception as e:
        print(f"解析API响应时出错: {e}")
        return {
            "overview": "解析失败",
            "relevance": "解析失败"
        }

def main():
    parser = argparse.ArgumentParser(description='使用DeepSeek分析论文数据')
    parser.add_argument('--api_key', type=str, help='DeepSeek API密钥')
    parser.add_argument('--input_file', type=str, default='data/cleaned/neurips_papers_1_cleaned.csv', 
                       help='输入CSV文件路径')
    parser.add_argument('--output_file', type=str, default='data/papers_1_analyzed.csv',
                       help='输出CSV文件路径')
    parser.add_argument('--sample', type=int, default=0,
                       help='只处理指定数量的论文样本，0表示处理全部')
    
    args = parser.parse_args()
    
    # 如果未通过命令行提供API密钥，则尝试从环境变量获取
    api_key = args.api_key or os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("必须提供DeepSeek API密钥，可通过--api_key参数或DEEPSEEK_API_KEY环境变量")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    
    # 读取CSV文件
    try:
        df = pd.read_csv(args.input_file)
        print(f"成功读取{len(df)}篇论文数据")
        
        # 如果指定了样本数量，则只处理部分数据
        if args.sample > 0:
            df = df.sample(min(args.sample, len(df)))
            print(f"随机抽样{len(df)}篇论文进行分析")
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        return
    
    # 分析论文
    results = []
    for i, row in tqdm(df.iterrows(), total=len(df), desc="分析论文"):
        title = row.get('title', '')
        clean_title = row.get('clean_title', title)  # 优先使用清洗后的标题
        abstract = row.get('abstract', '')
        authors = row.get('authors', '')
        
        print(f"\n处理论文 {i+1}/{len(df)}: {clean_title[:50]}...")
        
        # 调用API分析
        analysis = analyze_paper(api_key, clean_title, abstract, authors)
        
        # 添加到结果
        result_row = {
            'title': title,
            'clean_title': clean_title,
            'authors': authors,
            'abstract': abstract,
            'overview': analysis['overview'],
            'relevance': analysis['relevance']
        }
        results.append(result_row)
        
        # 避免API限制
        if i < len(df) - 1:
            delay = 1  # 根据API限制调整延迟时间
            print(f"等待{delay}秒...")
            time.sleep(delay)
    
    # 保存结果
    result_df = pd.DataFrame(results)
    result_df.to_csv(args.output_file, index=False, encoding='utf-8-sig')
    print(f"\n分析完成! 结果已保存到 {args.output_file}")
    
    # 输出高相关性论文摘要
    print("\n与研究方向高度相关的论文:")
    high_relevance = []
    for i, row in result_df.iterrows():
        relevance = row['relevance'].lower()
        if '高' in relevance or 'high' in relevance:
            high_relevance.append({
                'title': row['clean_title'],
                'overview': row['overview'],
                'relevance': row['relevance']
            })
    
    if high_relevance:
        for i, paper in enumerate(high_relevance):
            print(f"{i+1}. {paper['title']}")
            print(f"   概述: {paper['overview']}")
            print(f"   相关性: {paper['relevance']}")
            print("-" * 80)
    else:
        print("未找到高度相关的论文")

if __name__ == "__main__":
    main() 