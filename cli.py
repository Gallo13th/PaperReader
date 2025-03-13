import tqdm
from openai import OpenAI
import PyPDF2
import json
import os
import yaml
import argparse
# url = "https://api.siliconflow.cn/v1/chat/completions"
base_url = "https://api.siliconflow.cn/v1"

### pipline step 1: identify the text belongs to which part
##### part includes: title+abstract+introduction+related work; method; experiment; conclusion; reference
##### the text should be divided into 5 parts, and the text should be cleaned

def indentify_text_belong(pdf_path, workdir, api_key):
    cleaned_prompt =  """
我们将论文分为八个部分，分别是：
1. 标题
2. 摘要
3. 引言
4. 相关工作
5. 方法
6. 实验+结果
7. 结论+讨论+展望
8. 参考文献
我们输入的文本中，可能包括一个或多个部分，请**判断输入的文本中属于某一部分的文本**，并将其提取出来。
注意，**不要丢失原文文本内容**。
注意，**对于连词符加换行符的情况，需要将其合并为一个段落**。
注意，**不要删改原文内容，只需要提取出来即可**。
注意，**对于多数部分的切换，是会有明确的标题的**，但是**也有可能没有明确的标题，这时候需要根据上下文来判断**。
注意，**对于公式、表格等特殊内容，使用markdown的语法进行提取**。
注意。**确保内容的可读性，对于提取图表导致的大量空行和不连续的文本，应该选择忽略**
输出格式按照**json格式**，参考格式如下
    "title": "text",
    "abstract": "text",
    "introduction": "text",
    "related_work": "text",
    "method": "text",
    "experiment": "text",
    "conclusion": "text",
    "reference": "text"
对于上一段文本，你的分类结果如下：
{last_result}
输入文本如下：
{input_text}
"""

    base_url = "https://api.siliconflow.cn/v1"

    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )
    pdf_reader = PyPDF2.PdfReader(open(pdf_path, 'rb'))
    last_result = "暂无分类结果"
    results = {
        "title": "",
        "abstract": "",
        "introduction": "",
        "related_work": "",
        "method": "",
        "experiment": "",
        "conclusion": "",
        "reference": ""
    }
    idx = 0
    for page in tqdm.tqdm(pdf_reader.pages):
        if os.path.exists(workdir + '/text_belong_' + str(idx) + '.json'):
            idx += 1
            continue
        text = page.extract_text()
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-14B-Instruct",
            messages=[{'role': 'user', 'content': cleaned_prompt.format(last_result=last_result, input_text=text)}],
            stream=False,
            max_tokens=4096,
            response_format={"type": "json_object"},
            temperature=0.0,
            top_p=1.0,
            frequency_penalty=1.0,
            n=1,
        )
        tmp = ''
        tmp += response.choices[0].message.content
        last_result = tmp
        try:
            json_result = json.loads(last_result.encode('utf-8'), strict=False)
            json.dump(json_result, open(workdir + '/text_belong_' + str(idx) + '.json', 'w'))
        except:
            with open(workdir + '/text_belong_' + str(idx) + '.json', 'w') as f:
                f.write(last_result)
        idx += 1
    for i in range(idx):
        print(workdir + '/text_belong_' + str(i) + '.json')
        tmp_results = json.load(open(workdir + '/text_belong_' + str(i) + '.json', 'r'))
        for key in tmp_results:
            if tmp_results[key] == '' or tmp_results[key] is None:
                continue
            if key not in results:
                results[key] = tmp_results[key]
            else:
                results[key] += tmp_results[key]
    json.dump(results, open(workdir + '/text_belong.json', 'w'))
      
def summary_each_chapter(json_path, workdir, api_key):
    cleaned_prompt =  """
我们提供了文章的{chapter}部分，需要你对这部分内容进行清理和总结，不应该丢失重要的公式、模型结构等细节
对于标题内容，可能有大量重复，清理重复即可。
1. 删除所有非正文元素，包括：
- 页码及装饰符号（如*#等）
- 页眉/页脚文字（含网站链接、机构名称等）
- 致谢章节及参考文献/注释部分
- 论文声明、基金资助说明等补充信息
- 疑似从图中提取的文本

2. 完整保留所有学术内容：
- 章节标题及编号
- 段落文本（含公式、数据）
- 图表标题及说明文字
- 有序/无序列表项
- 保持原始文本顺序和格式不变

处理完成后，请直接输出清理后的完整文本，**使用markdown语法格式**，不要添加任何解释说明
对于公式内容，行内公式使用 $...$ 包裹，块级公式使用 $$...$$ 包裹
对于表格内容，使用markdown表格语法
文本如下：
{input_text}
"""

    base_url = "https://api.siliconflow.cn/v1"

    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    cleaned_json = json.load(open(json_path, 'r'))
    for key in cleaned_json:
        text = cleaned_json[key].encode('unicode_escape').decode('ascii') .encode('utf-8') 
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
            messages=[{'role': 'user', 'content': cleaned_prompt.format(chapter=key, input_text=text)}],
            stream=True,
            max_tokens=12384,
            response_format={"type": "text"},
            stop=None,
            temperature=0.3,
            top_p=0.9,
            frequency_penalty=1.0
        )
        tmp = ''
        with open(workdir + '/' + key + '.md', 'w') as f:
            pass

        for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            if chunk_message is None:
                continue
            tmp += chunk_message
            print(chunk_message, end='', flush=True, file=open(workdir + '/' + key + '.md', 'a'))

def argument_parser():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--config', type=str, default='./default_config.yaml', help='config file path')
    parser.add_argument('--api_key', type=str, help='api key')
    parser.add_argument('--pdf', type=str, help='pdf file path')
    parser.add_argument('--workdir', type=str, help='work directory')
    return parser.parse_args()

# for pdf in os.listdir('paper/'):
#     pdf_name = pdf.rstrip('.pdf')
#     n_pages = len(PyPDF2.PdfReader(open('paper/' + pdf, 'rb')).pages)
#     if n_pages > 20:
#         continue
#     os.makedirs(str('cleaned/' + pdf_name), exist_ok=True)
#     if os.path.exists('cleaned/' + pdf_name + '/text_belong.json'):
#         continue
#     indentify_text_belong('paper/' + pdf, 'cleaned/' + pdf_name + '/')
#     summary_each_chapter('cleaned/' + pdf_name + '/text_belong.json', 'cleaned/' + pdf_name + '/')
    
if __name__ == '__main__':
    args = argument_parser()
    config = yaml.load(open(args.config, 'r'),yaml.SafeLoader)
    os.makedirs(args.workdir, exist_ok=True)
    indentify_text_belong(args.pdf, args.workdir, args.api_key)
    summary_each_chapter(args.workdir + '/text_belong.json', args.workdir, args.api_key)