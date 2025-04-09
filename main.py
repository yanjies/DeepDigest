import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import csv
from urllib.parse import quote
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# 配置
MAX_WORKERS = 5  # 线程池大小
CSV_FILE = "neurips_papers.csv"
SKIP_TRANSLATION = True  # 设置为True跳过翻译

def translate_text(text):
    """占位翻译函数，当SKIP_TRANSLATION为True时直接返回空字符串"""
    if SKIP_TRANSLATION:
        return ""
    else:
        # 如果将来需要实现翻译，可以在这里添加实际的翻译逻辑
        return "翻译功能已禁用"

def fetch_papers_info(url):
    """抓取论文标题和摘要"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        papers_data = []
        # 查找论文块 - 根据页面结构调整选择器
        paper_blocks = soup.select('div[class^="#"]')
        
        if not paper_blocks:
            # 备选方案: 尝试找到所有论文条目
            paper_blocks = soup.find_all('div', {'class': lambda x: x and (x.startswith('paper-') or 'paper' in x)})
        
        if not paper_blocks:
            # 再次尝试通过结构推断
            headers = soup.find_all(['h2', 'h3'], {'id': lambda x: x and ('paper-' in x or '#' in x)})
            for header in headers:
                paper_info = {}
                paper_info['title'] = header.text.strip()
                authors_section = header.find_next('p')
                if authors_section and 'Authors' in authors_section.text:
                    paper_info['authors'] = authors_section.text.replace('Authors:', '').strip()
                abstract_section = authors_section.find_next('p') if authors_section else None
                if abstract_section:
                    paper_info['abstract'] = abstract_section.text.strip()
                papers_data.append(paper_info)
        
        # 如果上述方法都失败，尝试直接解析页面结构
        if not papers_data:
            # 尝试识别页面中的论文条目
            paper_entries = []
            for element in soup.find_all(['h1', 'h2', 'h3']):
                text = element.text.strip()
                if re.search(r'#\d+', text) or 'paper' in text.lower():
                    paper_entries.append(element)
            
            for entry in paper_entries:
                paper_info = {}
                title_text = entry.text.strip()
                # 处理标题中可能的编号和特殊字符
                paper_info['title'] = re.sub(r'^#\d+\s+', '', title_text)
                
                # 查找作者和摘要信息
                next_elem = entry.find_next_sibling()
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3']:
                    if 'Authors' in next_elem.text or 'authors' in next_elem.text.lower():
                        paper_info['authors'] = next_elem.text.replace('Authors:', '').strip()
                    elif 'abstract' not in paper_info and len(next_elem.text) > 100:
                        # 假设较长的文本块是摘要
                        paper_info['abstract'] = next_elem.text.strip()
                    next_elem = next_elem.find_next_sibling()
                
                if 'title' in paper_info:
                    papers_data.append(paper_info)
        
        return papers_data
    
    except Exception as e:
        print(f"抓取页面时出错: {e}")
        return []

def search_arxiv(title):
    """在arXiv上搜索论文并返回链接"""
    try:
        search_url = f"https://arxiv.org/search/?query={quote(title)}&searchtype=title"
        response = requests.get(search_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.select('.list-title > a')
        
        if results:
            paper_link = results[0]['href']
            if not paper_link.startswith('http'):
                paper_link = 'https://arxiv.org' + paper_link
            return paper_link
        else:
            return "未找到arXiv链接"
    
    except Exception as e:
        print(f"在arXiv搜索时出错: {e}")
        return "搜索arXiv时出错"

def process_paper(paper):
    """处理单个论文的所有步骤"""
    try:
        # 确保paper字典包含必要的键
        if 'title' not in paper:
            paper['title'] = ""
        if 'abstract' not in paper:
            paper['abstract'] = ""
        if 'authors' not in paper:
            paper['authors'] = ""
            
        # 获取arXiv链接
        arxiv_link = search_arxiv(paper['title'])
        paper['arxiv_link'] = arxiv_link
        
        # 添加空的翻译字段，稍后可以手动添加翻译
        if SKIP_TRANSLATION:
            paper['title_zh'] = ""
            paper['abstract_zh'] = ""
        else:
            paper['title_zh'] = translate_text(paper['title'])
            paper['abstract_zh'] = translate_text(paper['abstract'])
        
        return paper
    except Exception as e:
        print(f"处理论文时出错: {e}")
        # 返回原始论文信息，添加空翻译字段
        paper['arxiv_link'] = "处理出错"
        paper['title_zh'] = ""
        paper['abstract_zh'] = ""
        return paper

def main():
    # 要抓取的URL列表
    urls = [
        "https://papers.cool/venue/NeurIPS.2023?group=Spotlight&show=392",
        "https://papers.cool/venue/NeurIPS.2023?group=Oral&show=75",
        "https://papers.cool/venue/NeurIPS.2024?group=Spotlight&show=327",
        "https://papers.cool/venue/NeurIPS.2024?group=Oral&show=61"
    ]
    
    all_papers = []
    
    # 抓取所有页面
    for url in urls:
        print(f"正在抓取 {url}")
        try:
            papers = fetch_papers_info(url)
            all_papers.extend(papers)
            print(f"从 {url} 抓取了 {len(papers)} 篇论文")
        except Exception as e:
            print(f"抓取 {url} 时出错: {e}")
    
    print(f"总共抓取了 {len(all_papers)} 篇论文")
    
    if not all_papers:
        print("未找到任何论文，请检查网页结构或网络连接")
        return
    
    # 尝试使用自定义解析器和Selenium
    if len(all_papers) < 10:
        print("尝试使用备选抓取方法...")
        try:
            from alternate_scraper import fetch_papers_with_selenium
            selenium_papers = []
            for url in urls:
                papers = fetch_papers_with_selenium(url)
                selenium_papers.extend(papers)
            
            if len(selenium_papers) > len(all_papers):
                all_papers = selenium_papers
                print(f"使用Selenium抓取到 {len(all_papers)} 篇论文")
        except Exception as e:
            print(f"备选抓取方法失败: {e}")
    
    # 处理所有论文，带错误处理
    processed_papers = []
    for paper in tqdm(all_papers, desc="处理论文"):
        try:
            processed_paper = process_paper(paper)
            processed_papers.append(processed_paper)
        except Exception as e:
            print(f"处理论文 {paper.get('title', '未知标题')} 时出错: {e}")
            # 添加原始论文但标记为错误
            paper['arxiv_link'] = "处理出错"
            paper['title_zh'] = ""
            paper['abstract_zh'] = ""
            processed_papers.append(paper)
    
    # 保存到CSV
    try:
        df = pd.DataFrame(processed_papers)
        # 将列重新排序，使结构更清晰
        columns_order = ['title', 'authors', 'abstract', 'arxiv_link', 'title_zh', 'abstract_zh']
        # 确保所有必要的列都存在
        for col in columns_order:
            if col not in df.columns:
                df[col] = ""
        # 重新排序
        df = df[columns_order]
        df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
        print(f"所有数据已保存到 {CSV_FILE}")
        print(f"注意：翻译功能已跳过，title_zh和abstract_zh字段为空")
    except Exception as e:
        print(f"保存CSV文件时出错: {e}")
        # 尝试简单保存
        with open("neurips_papers_backup.csv", "w", encoding="utf-8") as f:
            for paper in processed_papers:
                f.write(f"{paper.get('title', '')}\t{paper.get('authors', '')}\t{paper.get('arxiv_link', '')}\n")
        print("备份数据已保存到 neurips_papers_backup.csv")

if __name__ == "__main__":
    main() 