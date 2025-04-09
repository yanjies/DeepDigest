import requests
import time

# 最简单的搜索，不使用任何复杂库
def simple_search(title):
    print(f"搜索标题: {title[:50]}...")
    try:
        # 简化的请求
        from urllib.parse import quote
        url = f"https://arxiv.org/search/?query={quote(title[:50])}&searchtype=title"
        
        print(f"请求URL: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            content = response.text[:200]  # 只取前200个字符
            print(f"内容预览: {content}...")
            return "搜索成功"
        else:
            return f"HTTP错误: {response.status_code}"
    except Exception as e:
        return f"搜索错误: {str(e)}"

# 测试一个简单标题
result = simple_search("Machine Learning")
print(f"结果: {result}") 