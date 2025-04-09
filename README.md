# DeepDigest

## 论文智能收集与分析工具

DeepDigest是一个自动化学术论文收集、清洗和分析的工具集，专注于帮助研究人员快速识别与特定研究方向相关的高价值论文。该工具通过一系列脚本组成完整的数据处理流水线，从网络抓取论文信息，进行数据清洗，使用大语言模型进行内容分析，并自动查找论文在arXiv上的链接。



## 功能特点

- 自动论文抓取：从指定网站（如NeurIPS会议页面）批量抓取论文信息
- 智能数据清洗：自动清理论文标题中的特殊标记和格式问题
- 深度内容分析：利用DeepSeek API分析论文内容和研究方向相关性
- arXiv链接检索：自动在arXiv上搜索并获取原始论文链接
- 相关性评估：自动识别并突出显示与目标研究领域高度相关的论文
- 分批处理：支持大规模数据的分批处理，自动保存中间结果
- 完整日志：详细记录每个步骤的执行情况，便于追踪和调试



### 安装步骤

```
# 克隆仓库
git clone https://github.com/你的用户名/DeepDigest.git
cd DeepDigest

# 安装依赖
pip install -r requirements.txt
```



## 使用方法

### 完整流水线执行

```
# 第1步：抓取论文
python step1_fetch_papers.py

# 第2步：清洗数据
python step2_clean_papers.py

# 第3步：使用DeepSeek分析论文（需要API密钥）
python step3_analyze_papers_with_deepseek.py --api_key YOUR_DEEPSEEK_API_KEY
# 或通过环境变量提供API密钥
# export DEEPSEEK_API_KEY=YOUR_KEY
# python step3_analyze_papers_with_deepseek.py

# 第4步：在arXiv上搜索论文链接
python step4_search_arxiv.py
```



### 单步骤执行示例

```
# 仅分析10篇指定论文
python step3_analyze_papers_with_deepseek.py --input_file data/cleaned/my_papers.csv --output_file data/my_analyzed_papers.csv --sample 10 --api_key YOUR_API_KEY
```



## Pipeline详解

DeepDigest由四个主要模块组成，形成完整的数据处理流水线：

1. 数据抓取 (step1_fetch_papers.py)
   - 功能：从指定URL抓取NeurIPS等会议的论文数据
   - 输入：预定义的论文来源URL
   - 输出：原始论文数据CSV文件
2. 数据清洗 (step2_clean_papers.py)
   - 功能：清理论文标题中的特殊标记和格式问题
   - 输入：原始论文数据
   - 输出：清洗后的论文数据CSV文件
3. 内容分析 (step3_analyze_papers_with_deepseek.py)
   - 功能：利用DeepSeek API分析论文内容和相关性
   - 输入：清洗后的论文数据，DeepSeek API密钥
   - 输出：包含论文概述和相关性评估的CSV文件
4. arXiv搜索 (step4_search_arxiv.py)
   - 功能：自动在arXiv上搜索论文并获取链接
   - 输入：论文清洗/分析后的数据
   - 输出：包含arXiv链接的CSV文件和高相关性论文列表



## 输出示例

```
与研究方向高度相关的论文:
1. Efficient Audio Representation Learning with Deep Masked Autoencoder
   概述: 该论文提出了一种用于音频表示学习的深度掩码自编码器，通过掩码重建任务实现高效预训练。
   相关性: 高度相关，直接探讨了音频预训练模型中最优片段长度的选择，并提出了基于信息瓶颈的训练数据筛选方法。
--------------------------------------------------------------------------------
```



## 数据目录结构

```
data/
  ├── neurips_papers_1.csv       # 原始抓取的论文数据
  ├── neurips_papers_1_cleaned.csv  # 清洗后的论文数据
  ├── papers_1_analyzed.csv      # 论文分析结果
  ├── papers_with_arxiv_chunk_1.csv  # arXiv搜索中间结果
  ├── papers_with_arxiv.csv      # 合并后的最终结果
  └── arxiv_search.log           # 搜索日志
```



## 注意事项

- API使用：DeepSeek API调用需要有效的API密钥，请在执行分析步骤前配置

- 爬虫限制：网站爬取功能设有随机延迟，以尊重网站访问策略

- 资源消耗：处理大量论文时，特别是arXiv搜索步骤可能需要较长时间

- 中间结果：系统会自动保存中间结果，以防程序中断导致数据丢失

- 内存管理：对于大型数据集，程序实现了分批处理和垃圾回收机制



## 贡献指南

欢迎对DeepDigest项目做出贡献！您可以通过以下方式参与：

1. 提交Bug报告或功能需求
2. 提交Pull Request改进代码
3. 完善文档和示例
4. 分享使用经验和改进建议



## 许可证

本项目采用MIT许可证。详见LICENSE文件。