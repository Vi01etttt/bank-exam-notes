"""用已核对的本地目录生成无脚本HTML，补齐下载状态。"""
from pathlib import Path
import hashlib, html, json, re
import markdown

ROOT=Path(__file__).resolve().parent
STYLE='body{max-width:1100px;margin:32px auto;padding:0 24px;font-family:"Microsoft YaHei",sans-serif;line-height:1.8;color:#172b4d}table{border-collapse:collapse;width:100%;display:block;overflow-x:auto}th,td{border:1px solid #ccd5df;padding:10px;vertical-align:top}a{color:#125cb0}h1,h2{line-height:1.4}pre{white-space:pre-wrap;background:#f3f6f9;padding:16px}code{overflow-wrap:anywhere}'

def render(text,title):
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+STYLE+'</style><body>'+markdown.markdown(text,extensions=['tables','fenced_code'])+'</body></html>'

record=(ROOT/'web-pages/粉笔与牛客公开信息.md').read_text(encoding='utf-8')
parts={}
for segment in record.split('\n## ')[1:]:
    name,body=segment.split('\n',1)
    parts[name]='# '+name+'\n\n保存日期：2026-10-03。浏览器公开信息离线整理，不含试卷正文。\n'+body
mapping={
 '粉笔_中国银行题库':'粉笔中国银行题库',
 '粉笔_互联网校招Java题库':'粉笔互联网校招Java题库',
 '粉笔_银行模拟题':'粉笔银行模拟题',
 '牛客_招行2018开发岗套卷':'牛客招商银行开发岗套卷',
 '牛客_招行2018测试岗套卷':'牛客招商银行测试岗套卷',
}
for stem,section in mapping.items():
    (ROOT/'web-pages'/f'{stem}.html').write_text(render(parts[section],section),encoding='utf-8')
catalog=(ROOT/'web-pages/牛客2018名企试题汇总离线索引.md').read_text(encoding='utf-8')
(ROOT/'web-pages/牛客_2018名企春招试题汇总.html').write_text(render(catalog,'牛客2018试题汇总离线索引'),encoding='utf-8')
for p in (ROOT/'web-pages').glob('*.md'):
    p.with_suffix('.html').write_text(render(p.read_text(encoding='utf-8'),p.stem),encoding='utf-8')
text=(ROOT/'README.md').read_text(encoding='utf-8')
for p in (ROOT/'web-pages').glob('*.md'):
    text=text.replace('web-pages/'+p.name,'web-pages/'+p.with_suffix('.html').name)
(ROOT/'离线阅读入口.html').write_text(render(text,'历年资料本地保存清单'),encoding='utf-8')

manifest=json.loads((ROOT/'下载清单.json').read_text(encoding='utf-8'))
for item in manifest:
    name=item['name']
    if name=='出版社_2009软设上午解析':
        item.update(status='PDF原文件已完整下载并核验',pdf_pages=31,visual_check='第18页渲染可读',scope='出版社公开样章；非整本书')
    elif name in mapping:
        item.update(status='仅保存浏览器公开目录或题型信息',scope='未取得登录后题目正文与解析',save_method='人工核对浏览器可见内容后生成离线HTML')
    elif name=='牛客_2018名企春招试题汇总':
        item.update(status='公开目录索引已保存',scope='原文章全部公司分组；不含各链接下试卷',save_method='浏览器正文整理，标题部分缩写')
    elif name=='信管网_2026年5月软设回忆题目录':
        item.update(status='两页40条目录摘要已保存，正文未取得',scope='39个题目链接返回文件未找到；1个请求失败',
                    additional_file='web-pages/信管网_40条回忆题目录.html')
    if 'file' in item:
        data=(ROOT/item['file']).read_bytes()
        item.update(saved_file_bytes=len(data),saved_file_sha256=hashlib.sha256(data).hexdigest())
    if 'sha256' in item: item['download_response_sha256']=item.pop('sha256')
(ROOT/'下载清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('已生成离线入口、目录HTML及准确的本地保存状态。')
