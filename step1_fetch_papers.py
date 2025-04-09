import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from tqdm import tqdm
import os

def fetch_papers_info(url):
    """抓取论文标题和摘要"""
    try:
        print(f"正在抓取 {url}")
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
        
        print(f"抓取到 {len(papers_data)} 篇论文")
        return papers_data
    
    except Exception as e:
        print(f"抓取页面时出错: {e}")
        return []

def try_alternative_method(url):
    """如果主方法失败，尝试使用Selenium"""
    try:
        from alternate_scraper import fetch_papers_with_selenium
        print("尝试使用Selenium抓取...")
        return fetch_papers_with_selenium(url)
    except Exception as e:
        print(f"备选抓取方法失败: {e}")
        return []

def main():
    # 创建数据目录
    if not os.path.exists('data'):
        os.makedirs('data')
        
    # 要抓取的URL列表
    urls = [
        "https://papers.cool/venue/NeurIPS.2023?group=Spotlight&show=392",
        "https://papers.cool/venue/NeurIPS.2023?group=Oral&show=75",
        "https://papers.cool/venue/NeurIPS.2024?group=Spotlight&show=327",
        "https://papers.cool/venue/NeurIPS.2024?group=Oral&show=61"
    ]
    
    # 抓取所有页面，每个链接保存为独立的CSV文件
    for i, url in enumerate(urls):
        # 生成文件名
        filename = f"data/neurips_papers_{i+1}.csv"
        
        # 抓取论文
        papers = fetch_papers_info(url)
        
        # 如果抓取失败，尝试备选方法
        if len(papers) < 10:
            alternative_papers = try_alternative_method(url)
            if len(alternative_papers) > len(papers):
                papers = alternative_papers
                print(f"使用备选方法抓取到 {len(papers)} 篇论文")
        
        # 保存到CSV
        if papers:
            df = pd.DataFrame(papers)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"保存 {len(papers)} 篇论文到 {filename}")
        else:
            print(f"未能从 {url} 抓取到论文")
    
    # 合并所有数据
    all_files = [f for f in os.listdir('data') if f.startswith('neurips_papers_') and f.endswith('.csv')]
    all_papers = []
    
    for file in all_files:
        df = pd.read_csv(os.path.join('data', file))
        all_papers.append(df)
    
    if all_papers:
        combined_df = pd.concat(all_papers, ignore_index=True)
        combined_df.to_csv('data/all_papers.csv', index=False, encoding='utf-8-sig')
        print(f"成功合并所有数据，共 {len(combined_df)} 篇论文")

if __name__ == "__main__":
    main() 