# 如果主方法不能正确抓取网页，这里提供一个备选的抓取方法
# 请注意：这个方法使用了Selenium，需要安装Chrome WebDriver

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

def fetch_papers_with_selenium(url):
    """使用Selenium抓取可能需要JavaScript渲染的页面"""
    options = Options()
    options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    # 等待页面加载
    time.sleep(5)
    
    # 获取页面内容
    html = driver.page_source
    driver.quit()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    papers_data = []
    # 根据实际页面结构调整选择器
    paper_sections = soup.find_all(['h2', 'h3'], {'id': True})
    
    for section in paper_sections:
        paper_info = {}
        paper_info['title'] = section.text.strip()
        
        current = section.next_sibling
        while current and not (current.name in ['h2', 'h3'] and current.get('id')):
            if 'Authors' in getattr(current, 'text', ''):
                paper_info['authors'] = current.text.replace('Authors:', '').strip()
            elif paper_info.get('authors') and not paper_info.get('abstract'):
                paper_info['abstract'] = current.text.strip()
            current = current.next_sibling
        
        papers_data.append(paper_info)
    
    return papers_data 