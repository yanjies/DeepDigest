import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import time
import random
from tqdm import tqdm
import os
import sys
import traceback
import gc  # 添加垃圾回收模块

# 减少全局变量的使用
CHUNK_SIZE = 5  # 每批只处理5篇论文，减小内存压力
DELAY_MIN = 10  # 增加延迟时间到10-15秒
DELAY_MAX = 15

def search_arxiv(title, retry_count=2, base_delay=10):
    """在arXiv上搜索论文并返回链接，包含重试机制"""
    if not title or len(title.strip()) == 0:
        return "标题为空"
    
    for attempt in range(retry_count):
        try:
            # 简化搜索查询，只使用标题的前60个字符减轻内存负担
            search_query = title[:60].strip()
            search_url = f"https://arxiv.org/search/?query={quote(search_query)}&searchtype=title"
            
            # 简化请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 设置较短的超时，防止长时间等待
            response = requests.get(search_url, headers=headers, timeout=20)
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"请求返回状态码: {response.status_code}")
                if attempt < retry_count - 1:
                    delay = base_delay + random.uniform(1, 5)
                    print(f"等待 {delay:.2f} 秒后重试...")
                    time.sleep(delay)
                    continue
                else:
                    return f"请求失败，状态码: {response.status_code}"
            
            # 使用较轻量的解析方法
            # 使用string方法而不是创建完整的BeautifulSoup对象
            html_text = response.text
            
            # 直接用字符串搜索查找arxiv链接
            if "No results found" in html_text or "没有找到结果" in html_text:
                return "未找到arXiv链接"
            
            # 简单地查找第一个arxiv链接
            import re
            arxiv_pattern = r'https://arxiv.org/abs/\d+\.\d+'
            matches = re.findall(arxiv_pattern, html_text)
            
            if matches:
                # 获取结果并立即清理
                result = matches[0]
                del html_text, matches
                gc.collect()  # 强制垃圾回收
                return result
            
            # 如果没有找到直接链接，再尝试更复杂的解析
            try:
                soup = BeautifulSoup(html_text, 'html.parser')
                
                # 查找结果
                results = soup.select('.list-title > a')
                
                if results:
                    paper_link = results[0]['href']
                    if not paper_link.startswith('http'):
                        paper_link = 'https://arxiv.org' + paper_link
                    
                    # 清理资源
                    del soup, results, html_text
                    gc.collect()
                    return paper_link
                
                # 清理不再需要的资源
                del soup
            except Exception as parser_error:
                print(f"解析HTML时出错: {parser_error}")
            
            # 如果上面的方法都失败，返回未找到
            return "未找到arXiv链接"
                
        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
            if attempt < retry_count - 1:
                delay = base_delay + random.uniform(3, 8)
                print(f"等待 {delay:.2f} 秒后重试...")
                time.sleep(delay)
            else:
                return f"搜索arXiv时网络错误"
        except Exception as e:
            print(f"在arXiv搜索时出错: {e}")
            if attempt < retry_count - 1:
                delay = base_delay + random.uniform(3, 8)
                print(f"等待 {delay:.2f} 秒后重试...")
                time.sleep(delay)
            else:
                return f"搜索arXiv时出错"
        
        # 每次尝试后进行垃圾回收
        gc.collect()

def safe_search_arxiv(title):
    """安全包装搜索函数，确保任何异常都被捕获"""
    try:
        return search_arxiv(title)
    except Exception as e:
        print(f"搜索过程中发生未预期错误: {e}")
        return "搜索时发生错误"

def main():
    # 检查数据目录
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # 简化日志记录
    log_file = 'data/arxiv_search.log'
    log_handle = open(log_file, 'a', encoding='utf-8')
    
    def log_message(msg):
        """同时记录到控制台和日志文件"""
        print(msg)
        log_handle.write(f"{msg}\n")
        log_handle.flush()  # 立即写入磁盘
    
    log_message(f"=== 开始执行arXiv搜索 {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
    
    try:
        # 读取清洗后的论文
        input_file = 'data/cleaned_papers.csv'
        if not os.path.exists(input_file):
            log_message(f"错误: 未找到文件 {input_file}")
            log_handle.close()
            return
        
        # 使用更节省内存的方式读取CSV
        # 使用迭代器而不是一次性加载整个DataFrame
        log_message("开始读取数据文件...")
        
        # 首先确定文件中有多少行
        with open(input_file, 'r', encoding='utf-8') as f:
            row_count = sum(1 for _ in f) - 1  # 减去标题行
        
        log_message(f"文件中包含 {row_count} 篇论文")
        
        # 检查是否有已完成的中间结果
        chunk_files = [f for f in os.listdir('data') if f.startswith('papers_with_arxiv_chunk_') and f.endswith('.csv')]
        processed_titles = set()
        
        if chunk_files:
            log_message(f"发现 {len(chunk_files)} 个已处理的批次文件")
            
            # 读取已处理的论文标题
            for chunk_file in chunk_files:
                try:
                    chunk_df = pd.read_csv(os.path.join('data', chunk_file), usecols=['title'])
                    for title in chunk_df['title']:
                        processed_titles.add(title)
                except Exception as e:
                    log_message(f"读取已处理文件 {chunk_file} 时出错: {e}")
            
            log_message(f"已处理 {len(processed_titles)} 篇论文")
        
        # 使用分块读取CSV文件
        chunk_id = len(chunk_files) + 1
        total_processed = 0
        
        for df_chunk in pd.read_csv(input_file, chunksize=CHUNK_SIZE):
            chunk_results = []
            
            log_message(f"处理第 {chunk_id} 批论文 (共 {len(df_chunk)} 篇)")
            
            for _, row in df_chunk.iterrows():
                title = row['title']
                
                # 如果已经处理过，跳过
                if title in processed_titles:
                    log_message(f"跳过已处理的论文: {title[:30]}...")
                    continue
                
                log_message(f"处理论文: {title[:50]}...")
                
                try:
                    # 获取清洗后的标题
                    clean_title = row['clean_title']
                    log_message(f"使用清洗后的标题: {clean_title[:50]}...")
                    
                    # 搜索arXiv
                    arxiv_link = safe_search_arxiv(clean_title)
                    log_message(f"找到链接: {arxiv_link}")
                    
                    # 添加到结果
                    chunk_results.append({
                        'title': title,
                        'clean_title': clean_title,
                        'authors': row.get('authors', ''),
                        'abstract': row.get('abstract', ''),
                        'arxiv_link': arxiv_link
                    })
                    
                    # 记录为已处理
                    processed_titles.add(title)
                    total_processed += 1
                    
                    # 强制垃圾回收
                    gc.collect()
                    
                except Exception as e:
                    log_message(f"处理论文时出错: {str(e)}")
                    traceback.print_exc(file=log_handle)
                
                # 每篇论文之间等待较长时间
                delay = random.uniform(DELAY_MIN, DELAY_MAX)
                log_message(f"等待 {delay:.2f} 秒...")
                time.sleep(delay)
            
            # 保存这一批的中间结果
            if chunk_results:
                temp_file = f'data/papers_with_arxiv_chunk_{chunk_id}.csv'
                pd.DataFrame(chunk_results).to_csv(temp_file, index=False, encoding='utf-8-sig')
                log_message(f"保存中间结果到 {temp_file}")
            
            # 清理这一批的内存
            del chunk_results, df_chunk
            gc.collect()
            
            chunk_id += 1
            
            log_message(f"已处理总数: {total_processed}/{row_count}")
        
        # 合并所有结果
        log_message("处理完成，开始合并所有结果...")
        merge_all_chunks('data')
        
    except Exception as e:
        log_message(f"执行过程中发生错误: {e}")
        traceback.print_exc(file=log_handle)
    
    finally:
        log_message(f"=== 完成执行 {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
        log_handle.close()

def merge_all_chunks(data_dir):
    """合并所有分块结果文件"""
    chunk_files = [f for f in os.listdir(data_dir) if f.startswith('papers_with_arxiv_chunk_') and f.endswith('.csv')]
    
    if not chunk_files:
        print("没有找到任何分块结果文件")
        return
    
    print(f"开始合并 {len(chunk_files)} 个分块结果文件...")
    
    # 逐个读取并合并文件，以减少内存使用
    all_data = []
    for file in chunk_files:
        file_path = os.path.join(data_dir, file)
        try:
            df = pd.read_csv(file_path)
            all_data.append(df)
            print(f"读取文件 {file}，包含 {len(df)} 行数据")
        except Exception as e:
            print(f"读取文件 {file} 时出错: {e}")
    
    if all_data:
        # 合并所有数据框
        combined_df = pd.concat(all_data, ignore_index=True)
        output_file = os.path.join(data_dir, 'papers_with_arxiv.csv')
        combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        # 统计找到了多少arXiv链接
        found_count = sum(1 for link in combined_df['arxiv_link'] if link != "未找到arXiv链接" and not link.startswith("搜索arXiv时"))
        
        print(f"合并完成! 在 {len(combined_df)} 篇论文中找到了 {found_count} 个arXiv链接")
        print(f"结果已保存到 {output_file}")
    else:
        print("没有有效的数据可以合并")

# 如果作为脚本直接运行
if __name__ == "__main__":
    # 设置垃圾回收阈值
    gc.set_threshold(100, 5, 5)  # 更积极的垃圾回收
    main()