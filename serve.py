#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YZH的Blog 本地预览服务器
用法:
    uv run serve.py                 # 默认端口 8000
    uv run serve.py -p 9000         # 指定端口
    uv run serve.py --no-open       # 不自动打开浏览器
"""
import argparse
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DIR = ROOT / "site"


def make_handler(directory: Path):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

        def log_message(self, fmt, *args):
            # 安静模式：只记录异常请求（4xx/5xx），正常访问不刷屏
            first = str(args[0]) if args else ""
            if first.isdigit() and int(first) >= 400:
                print(f"  [{self.log_date_time_string()}] {self.requestline} → {first}")

        def send_error(self, code, message=None, explain=None):
            # 404 时返回站点的终端风 404 页
            if code == 404:
                p404 = Path(self.directory) / "404.html"
                if p404.exists():
                    body = p404.read_bytes()
                    self.send_response(404)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
            super().send_error(code, message, explain)

    return Handler


def main(port: int | None = None, directory: Path | None = None, open_browser: bool = True) -> None:
    directory = directory or DEFAULT_DIR
    if not directory.exists():
        print(f"✗ 输出目录不存在: {directory}")
        print("  请先运行 uv run build.py 构建站点")
        raise SystemExit(1)

    port = port or 8000
    handler = make_handler(directory)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"✓ 预览地址: {url}")
    print(f"  （站点目录: {directory}）")
    print("  Ctrl+C 停止")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="YZH的Blog 本地预览")
    ap.add_argument("-p", "--port", type=int, default=8000, help="端口（默认 8000）")
    ap.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    args = ap.parse_args()
    main(port=args.port, open_browser=not args.no_open)
