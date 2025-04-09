import pandas as pd
import re
import os

def clean_title(title):
    """清洗论文标题，移除[PDF]等标记"""
    if not isinstance(title, str):
        return ""
    
    # 替换换行符为空格
    title = title.replace('\n', ' ')
    
    # 移除方括号内的内容，如[PDF20]、[Copy]、[Kimi26]、[REL]等
    cleaned_title = re.sub(r'\s*\[[^\]]*\]\s*', ' ', title)
    
    # 移除多余空格
    cleaned_title = re.sub(r'\s+', ' ', cleaned_title).strip()
    
    return cleaned_title

def main():
    # 检查数据目录
    if not os.path.exists('data'):
        print("错误: 未找到数据目录。请先运行fetch_papers.py")
        return
        
    # 读取所有论文
    # input_file = 'data/all_papers.csv'
    input_file = 'data/neurips_papers_1.csv'
    if not os.path.exists(input_file):
        print(f"错误: 未找到文件 {input_file}")
        return
        
    # 读取数据，处理潜在的解析错误
    try:
        df = pd.read_csv(input_file, on_bad_lines='skip')
        print(f"读取了 {len(df)} 篇论文")
    except Exception as e:
        print(f"读取CSV文件时出错: {e}")
        try:
            # 尝试另一种方式读取
            df = pd.read_csv(input_file, engine='python')
            print(f"使用Python引擎读取了 {len(df)} 篇论文")
        except Exception as e:
            print(f"使用Python引擎读取失败: {e}")
            return
    
    # 显示一些原始数据样例
    print("\n原始数据样例:")
    for i, row in df.head(3).iterrows():
        title = row.get('title', 'N/A')
        print(f"{i+1}. 标题: {title}")
        print(f"   作者: {row.get('authors', 'N/A')}")
        print(f"   摘要: {str(row.get('abstract', 'N/A'))[:100]}...\n")
    
    # 检查并处理列名
    if 'title' not in df.columns:
        print("错误: 未找到标题列。现有列:", df.columns.tolist())
        # 尝试找到可能的标题列
        possible_title_cols = [col for col in df.columns if 'title' in col.lower()]
        if possible_title_cols:
            print(f"使用 {possible_title_cols[0]} 作为标题列")
            df.rename(columns={possible_title_cols[0]: 'title'}, inplace=True)
        else:
            return
    
    # 清洗标题
    print("开始清洗标题...")
    df['clean_title'] = df['title'].apply(clean_title)
    
    # 显示清洗后的几个标题样例
    print("\n清洗前后的标题样例:")
    for i, (original, cleaned) in enumerate(zip(df['title'].head(5), df['clean_title'].head(5))):
        print(f"{i+1}. 原标题: {original}")
        print(f"   清洗后: {cleaned}")
        print("-" * 50)
    
    # 显示处理统计信息
    print("\n处理统计:")
    total = len(df)
    empty_before = df['title'].isna().sum() + (df['title'] == '').sum()
    empty_after = df['clean_title'].isna().sum() + (df['clean_title'] == '').sum()
    print(f"总论文数: {total}")
    print(f"清洗前空标题数: {empty_before}")
    print(f"清洗后空标题数: {empty_after}")
    
    # 保存清洗后的数据
    # output_file = 'data/cleaned_papers.csv'
    output_file = 'data/neurips_papers_1_cleaned.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n清洗后的数据已保存到 {output_file}")

if __name__ == "__main__":
    main() 