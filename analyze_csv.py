import pandas as pd

# 读取CSV文件，仅处理前5行
try:
    print("尝试读取CSV文件...")
    df = pd.read_csv('data/cleaned_papers.csv', nrows=5)
    print(f"成功读取了{len(df)}行数据")
    
    # 显示数据概要
    print("\n数据概要:")
    for i, row in df.iterrows():
        print(f"论文 {i+1}: {row.get('title', '')[:50]}...")
    
    print("\n读取成功！")
except Exception as e:
    print(f"读取失败: {e}") 