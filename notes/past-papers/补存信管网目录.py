"""保存指定回忆卷两页目录，核对其40个公开题目链接。"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import hashlib, html, json, re, urllib.request

ROOT = Path(__file__).resolve().parent
START = 'https://m.cnitpm.com/exam/ExamST.aspx?sid=14505743&t1=4'

def read(url):
    with urllib.request.urlopen(url, timeout=15) as response:
        data = response.read(5 * 1024 * 1024)
    return BeautifulSoup(data, 'html.parser')

def check(item):
    try:
        soup=read(item['url'])
        for tag in soup(['script','style','iframe']): tag.decompose()
        text=soup.get_text('\n',strip=True)
        if '文件未找到' in text or '已经被移走或删除' in text:
            item['status']='未取得正文：源站返回文件未找到'
        else:
            p=ROOT/'web-pages'/'信管网单题'/f"第{item['number']:02d}题.html"
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('<!doctype html><meta charset="utf-8"><title>公开单题快照</title>'
                         '<p>仅公开文字，图片与登录后解析未包含。来源：'+html.escape(item['url'])+
                         '</p><pre style="white-space:pre-wrap">'+html.escape(text)+'</pre>',encoding='utf-8')
            item.update(status='公开文字已保存，题干及解析完整性待核验',file=p.relative_to(ROOT).as_posix())
    except Exception as exc: item['status']='未取得正文：'+type(exc).__name__
    return item

first=read(START)
next_url=next(urljoin(START,a['href']) for a in first.find_all('a',href=True) if a.get_text(strip=True)=='下一页')
pages=[first,read(next_url)]
items={}
for soup in pages:
    for a in soup.find_all('a',href=True):
        title=a.get_text(' ',strip=True)
        match=re.match(r'第\s*(\d+)\s*道试题',title)
        if match: items[int(match[1])]={'number':int(match[1]),'excerpt':title,'url':urljoin(START,a['href'])}
with ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(check,items.values()))
(ROOT/'信管网题目链接核查.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 信管网2026年5月软件设计师回忆题目录','',
       '保存日期：2026-10-03。两页公开目录合并；以下是目录摘要，不是完整题干或答案。',
       '',f'[原目录第1页]({START}) · [原目录第2页]({next_url})','']
for x in results:
    lines.extend([f"## 第{x['number']}题",'',x['excerpt'],'',f"[原网页]({x['url']})；{x['status']}。",''])
(ROOT/'web-pages'/'信管网_40条回忆题目录.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({'catalog_items':len(results),'saved_question_pages':sum('file' in x for x in results),
                  'status_counts':{s:sum(x['status']==s for x in results) for s in {x['status'] for x in results}}},ensure_ascii=False))
