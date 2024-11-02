from openai import OpenAI
from os import getenv
import os
from datetime import datetime,timedelta
import pandas as pd
import re
import random
from dotenv import load_dotenv
load_dotenv()
# gets API Key from environment variable OPENAI_API_KEY
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.environ["OPENROUTER_KEY"],
)

# 对 Prompt 进行建模
# - 关键字 1
# - 文体
# - 模仿作家
# - 结局

def get_random_setup(sheet, excel_file = 'data.xlsx'):
    df = pd.read_excel(excel_file, sheet_name=sheet, header=None)
    
    # 获取第一列的所有值
    first_column = df[0].tolist()
    
    # 随机返回一个值
    return random.choice(first_column)

def create_prompt():
    PROMPT = f"""根据我提供的故事元素，你的任务是创作一部精彩、迷人且拥有600字左右的短篇故事。建议你以细腻的笔触处理每一处细节，并以优雅而生动的语言呈现故事的魅力。请详实地描绘每个角色，展示出他们的性格特点以及在故事中的地位和作用。你可以通过具体而生动的描述塑造情节，使读者对角色产生共鸣。

是时候显现你那专业作家的技巧了，让你的故事生动有趣，充满启发性。期待你能巧妙地将我提供的所有故事元素融入故事情节中，而且希望你能根据这些元素特性提出独特的创新理念，这样可以进一步丰富故事的内容，给读者带来愉快的阅读体验。

请确保你的短篇故事完整连贯，故事叙述逻辑清晰，从开始到结束一气呵成。你的目标是创作一部可以在轻松愉快的阅读环境中启发读者深思的故事。

以下是要求:

- 关键字：{get_random_setup('形容词')}{get_random_setup('关键字')}
- {get_random_setup('小说类型')}
- {get_random_setup('文笔风格')}
- {get_random_setup('结局')}
- {get_random_setup('其他要求')}

用 Markdown 文本的格式输出给我，不需要其他信息。

- slug: 标题英文slug
- categories 和 tags 都尽量多一点

Example format:
```markdown
---
title: 隐晦有深意的中文标题
author: Xiaowen Zhang
date: 2023-01-01T07:00:00+08:00
slug: title-in-english
type: post
categories:
  - 
tags:
  - tag1
  - tag2
draft: false
---

文章内容在这里
```
"""
    return PROMPT



def generate_article():

    completion = client.chat.completions.create(
    extra_headers={
        "HTTP-Referer": "https://storywith.in", # Optional, for including your app on openrouter.ai rankings.
        "X-Title": "Story Within", # Optional. Shows in rankings on openrouter.ai.
    },
    #model="qwen/qwen-2.5-72b-instruct",
    model="anthropic/claude-3.5-sonnet",
    messages=[
        {
        "role": "user",
        "content": create_prompt()
        }
    ]
    )
    #print(completion.choices[0].message.content)

    markdown_content = extract_markdown_content(completion.choices[0].message.content)

    return markdown_content



def extract_markdown_content(text):
    # Find the last occurrence of opening frontmatter "---"
    lines = text.splitlines()
    first_frontmatter = -1
    last_frontmatter = -1
    
    # Find the first and second "---"
    found_first = False
    for i in range(len(lines)):
        if lines[i].strip() == "---":
            if not found_first:
                first_frontmatter = i
                found_first = True
            else:
                last_frontmatter = i
                break
    
    if first_frontmatter == -1 or last_frontmatter == -1:
        return ""
    
    # Extract content starting from the first frontmatter
    content = lines[first_frontmatter:]
    
    # Remove any trailing ```
    while content and content[-1].strip() == "```":
        content.pop()
    
    # Join the lines back together
    return "\n".join(content)



def update_frontmatter(content: str, use_date=datetime.now()) -> str:
    # Get current date in YYYY-MM-DD format
    current_date_str = use_date.strftime('%Y-%m-%d')
    
    # Regular expression to match the date in frontmatter
    pattern = r'(date:\s*)(\d{4}-\d{2}-\d{2})(T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2})'
    
    # Replace only the date part while keeping time and timezone
    updated_content = re.sub(pattern, rf'\g<1>{current_date_str}\g<3>', content)
    
    return updated_content

def save_article(content, use_date=datetime.now()):
    if not content:
        return False
    
    year = use_date.strftime("%Y")
    date = use_date.strftime("%Y-%m-%d")

    content_updated = update_frontmatter(content, use_date)
    
    # 创建目录结构
    dir_path = f"./content/posts/{year}"
    os.makedirs(dir_path, exist_ok=True)
    
    # 检查文件是否存在，如果存在则添加后缀
    counter = 0
    while True:
        if counter == 0:
            file_path = f"{dir_path}/{date}.md"
        else:
            file_path = f"{dir_path}/{date}-{counter:02d}.md"
            
        if not os.path.exists(file_path):
            break
        counter += 1
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content_updated)
        print(f"Article saved successfully at: {file_path}")
        return True
    except Exception as e:
        print(f"Error saving article: {e}")
        return False

def process(use_date):
    # 生成文章
    article_content = generate_article()
    
    # 保存文章
    if article_content:
        save_article(article_content, use_date)
    else:
        print("Failed to generate article")

def batch_process(from_date=datetime.now(), to_date=datetime.now()):
    current_date = from_date
    while current_date <= to_date:
        print(f'Process Date: {current_date.strftime("%Y-%m-%d")}')
        process(current_date)
        process(current_date)
        process(current_date)
        current_date += timedelta(days=1)


if __name__ == "__main__":
    str_from = "2024-11-02"
    str_to = "2024-11-02"
    from_date=datetime.strptime(str_from, '%Y-%m-%d')
    to_date=datetime.strptime(str_to, '%Y-%m-%d')

    batch_process(from_date, to_date)