"""下载已核查的公开资料；不登录、不访问隐藏接口。"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import html
import json
import urllib.request
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
SOURCES = [
    ('出版社_2009软设上午解析', 'https://www.tup.com.cn/upload/books/yz/075339-01.pdf', 'pdf'),
    ('牛客_2018名企春招试题汇总', 'https://hr.nowcoder.com/article/1581', 'html'),
    ('信管网_2026年5月软设回忆题目录', 'https://m.cnitpm.com/exam/ExamST.aspx?sid=14505743&t1=4', 'html'),
    ('粉笔_中国银行题库', 'https://www.fenbi.com/spa/tiku/guide/home/yhzp/yhzp?labelId=3252', 'html'),
    ('粉笔_互联网校招Java题库', 'https://www.fenbi.com/spa/tiku/guide/home/itxz0/itxz0?labelId=3326', 'html'),
    ('粉笔_银行模拟题', 'https://www.fenbi.com/spa/tiku/guide/home/yhzp/yhzp?labelId=5884', 'html'),
    ('牛客_招行2018开发岗套卷', 'https://www.nowcoder.com/exam/test/11938764/summary', 'html'),
    ('牛客_招行2018测试岗套卷', 'https://www.nowcoder.com/exam/test/11939349/summary', 'html'),
    ('优就业_2016上半年软设上午卷_待核验', 'https://www.ujiuye.com/uploadfile/2021/0402/20210402104345787.pdf', 'pdf'),
]

def fetch(source):
    name, url, kind = source
    entry = {'name': name, 'url': url, 'checked_at_utc': datetime.now(timezone.utc).isoformat()}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=25) as response:
            data = response.read(30 * 1024 * 1024 + 1)
            entry.update(final_url=response.url, http_status=response.status,
                         content_type=response.headers.get('Content-Type', ''))
        if len(data) > 30 * 1024 * 1024:
            raise ValueError('文件超过本脚本30MB下载上限')
        entry.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        if kind == 'pdf':
            if not data.startswith(b'%PDF-'):
                raise ValueError('返回内容不是PDF，未保存为试卷')
            path = ROOT / 'PDF' / (name + '.pdf')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            entry.update(status='PDF已下载待结构核验', file=path.relative_to(ROOT).as_posix())
        else:
            soup = BeautifulSoup(data, 'html.parser')
            title = soup.title.get_text(' ', strip=True) if soup.title else name
            for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg']):
                tag.decompose()
            text = soup.get_text('\n', strip=True)
            path = ROOT / 'web-pages' / (name + '.html')
            path.parent.mkdir(parents=True, exist_ok=True)
            # 不保留可执行脚本，离线打开不会自动请求远程页面。
            out = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8">'
                   '<meta name="viewport" content="width=device-width,initial-scale=1">'
                   '<title>' + html.escape(title) + '</title><style>'
                   'body{max-width:960px;margin:32px auto;padding:0 24px;line-height:1.8;'
                   'font-family:"Microsoft YaHei",sans-serif}pre{white-space:pre-wrap;'
                   'overflow-wrap:anywhere;font-family:inherit}.notice{background:#fff3cd;padding:16px}'
                   '</style><h1>' + html.escape(name) + '</h1><p class="notice">'
                   '公开HTML的离线文字快照。动态内容、登录后试题、图片和在线交互可能未包含；'
                   '请以本地README中的保存范围为准。</p><p>来源：<a href="' +
                   html.escape(url, quote=True) + '">' + html.escape(url) + '</a></p><pre>' +
                   html.escape(text) + '</pre></html>')
            path.write_text(out, encoding='utf-8')
            entry.update(status='公开文字快照已保存，完整性待核验', file=path.relative_to(ROOT).as_posix(),
                         visible_text_chars=len(text), title=title)
    except Exception as exc:
        entry.update(status='未取得', error=f'{type(exc).__name__}: {exc}')
    return entry

if __name__ == '__main__':
    ROOT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, SOURCES))
    (ROOT / '下载清单.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    for item in results:
        print(json.dumps(item, ensure_ascii=False))
