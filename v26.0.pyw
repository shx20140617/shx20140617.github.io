#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
难猜的卡搭 V26.0
作者：@难猜的用户、@Deepseek
功能：图形界面版卡搭作品下载器，支持网页直链与本地 JSON 转换
"""

import json
import os
import re
import sys
import tempfile
import threading
import time
import zipfile
import webbrowser
from datetime import datetime
from queue import Queue
from tkinter import *
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ------------------------------------------------------------
# 依赖检查（requests）
# ------------------------------------------------------------
try:
    import requests
except ModuleNotFoundError:
    root = Tk()
    root.withdraw()
    messagebox.showerror(
        "缺少依赖",
        "未安装 requests 模块，请运行以下命令安装：\n\n"
        "pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple/"
    )
    sys.exit(1)

# ------------------------------------------------------------
# 常量定义
# ------------------------------------------------------------
VERSION = "V26.0"
DEFAULT_ASSET_STORE = "https://steam.nosdn.127.net/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_TIMEOUT = 20
DOWNLOAD_RETRIES = 3
RETRY_DELAY = 1

# 作者信息（点击跳转）
AUTHOR_INFO = [
    {"name": "@难猜的用户", "url": "https://www.ccw.site/student/6400af412806993182217040"},
    {"name": "@Deepseek", "url": "https://www.deepseek.com"}
]
CONTACT = "问题反馈：在“难猜的卡搭”发布中心的评论区反馈或在更新说明底部反馈，也可在我的个人主页留言板下反馈"
VERSION_NOTES_URL = "https://learn.ccw.site/article/cedc38e2-fc59-4ea4-b8aa-d4ec266df353"

# ------------------------------------------------------------
# URL 规范化（核心修复）
# ------------------------------------------------------------
def normalize_url(url, default_protocol="https:"):
    """将 URL 补全为绝对地址，无法补全时返回 None"""
    if not url:
        return None
    url = url.strip()
    if url.startswith('https://'):
        return url
    if url.startswith('http://'):
        return 'https://' + url[7:]
    if url.startswith('//'):
        return default_protocol + url
    if url.startswith('/'):
        return None
    return default_protocol + '//' + url

# ------------------------------------------------------------
# JSON 递归处理（完全保留原逻辑）
# ------------------------------------------------------------
def find_asset_pairs(data):
    pairs = set()
    if isinstance(data, dict):
        if 'assetId' in data and 'dataFormat' in data:
            pairs.add((data['assetId'], data['dataFormat']))
        for v in data.values():
            pairs.update(find_asset_pairs(v))
    elif isinstance(data, list):
        for item in data:
            pairs.update(find_asset_pairs(item))
    return pairs

def remove_hyphens_from_asset_fields(obj):
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in ('assetId', 'md5ext') and isinstance(v, str):
                obj[k] = v.replace('-', '')
            else:
                remove_hyphens_from_asset_fields(v)
    elif isinstance(obj, list):
        for item in obj:
            remove_hyphens_from_asset_fields(item)

def collect_asset_store_mapping(data):
    mapping = {}
    def _walk(obj):
        if isinstance(obj, dict):
            if 'assetId' in obj and isinstance(obj['assetId'], str):
                asset_id = obj['assetId']
                if 'assetStore' in obj and asset_id not in mapping:
                    store_url = normalize_url(obj['assetStore'])
                    if store_url:
                        mapping[asset_id] = store_url
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)
    _walk(data)
    return mapping

# ------------------------------------------------------------
# 网络请求（带重试）
# ------------------------------------------------------------
def download_file(url, dest_path):
    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        try:
            headers = {'User-Agent': USER_AGENT}
            resp = requests.get(url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception:
            if attempt < DOWNLOAD_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return False
    return False

def download_json_from_url(url):
    try:
        headers = {'User-Agent': USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise RuntimeError(f"无法下载或解析 project.json：{e}")

# ------------------------------------------------------------
# 卡搭页面解析
# ------------------------------------------------------------
def extract_project_info_from_kada_page(page_url):
    try:
        headers = {'User-Agent': USER_AGENT}
        resp = requests.get(page_url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        raise RuntimeError(f"无法获取页面：{e}")

    json_str = None
    # 方法1：括号匹配
    start_marker = 'window.pageData'
    start_idx = html.find(start_marker)
    if start_idx != -1:
        brace_start = html.find('{', start_idx)
        if brace_start != -1:
            count = 0
            in_string = False
            escape = False
            end_idx = -1
            for i in range(brace_start, len(html)):
                ch = html[i]
                if not in_string:
                    if ch == '{':
                        count += 1
                    elif ch == '}':
                        count -= 1
                        if count == 0:
                            end_idx = i
                            break
                if ch == '"' and not escape:
                    in_string = not in_string
                escape = (ch == '\\' and not escape)
            if end_idx != -1:
                json_str = html[brace_start:end_idx+1]
    # 方法2：正则
    if not json_str:
        pattern = r'window\.pageData\s*=\s*({.*?});'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            json_str = match.group(1)

    if not json_str:
        raise RuntimeError("未找到 window.pageData，页面结构可能已变化")

    try:
        page_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"解析 window.pageData 失败：{e}")

    project_url = page_data.get('projectUrl')
    if not project_url:
        raise RuntimeError("window.pageData 中不存在 projectUrl")

    project_name = page_data.get('name', '未知作品名')
    author_name = page_data.get('authorName', '未知作者')
    project_url = normalize_url(project_url) or project_url
    return project_url, project_name, author_name

def modify_kada_url(original_url):
    if original_url.startswith('https://kada.163.com/project/'):
        return original_url.replace(
            'https://kada.163.com/project/',
            'https://kada.163.com/h5/project/',
            1
        )
    return original_url

# ------------------------------------------------------------
# 核心打包引擎（GUI 回调版）
# ------------------------------------------------------------
def build_sb3_from_project_data(project_data, output_sb3_path,
                                log_callback=print, progress_callback=None):
    """
    增强版打包函数，支持通过回调输出日志和更新进度
    :param project_data: 解析后的 project.json 对象
    :param output_sb3_path: 输出文件路径
    :param log_callback: 日志输出函数，接收字符串
    :param progress_callback: 进度更新函数，接收当前/总数
    """
    original_pairs = find_asset_pairs(project_data)
    total_assets = len(original_pairs)
    log_callback(f"📦 共发现 {total_assets} 个素材资源")

    asset_store_map = collect_asset_store_mapping(project_data)
    log_callback(f"🗂️  其中 {len(asset_store_map)} 个素材拥有专属存储源")

    remove_hyphens_from_asset_fields(project_data)

    temp_dir = tempfile.mkdtemp(prefix="kada_downloader_")
    log_callback(f"📁 创建临时文件夹：{temp_dir}")

    try:
        json_dest = os.path.join(temp_dir, "project.json")
        with open(json_dest, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, separators=(',', ':'))
        log_callback("✅ 已写入优化后的 project.json")

        success_count = 0
        fail_count = 0

        for idx, (asset_id, data_fmt) in enumerate(original_pairs, start=1):
            clean_asset_id = asset_id.replace('-', '')
            filename = f"{clean_asset_id}.{data_fmt}"
            dest = os.path.join(temp_dir, filename)

            store_url = asset_store_map.get(asset_id)
            if not store_url or not (store_url.startswith('http://') or store_url.startswith('https://')):
                store_url = DEFAULT_ASSET_STORE
            store_url = store_url.rstrip('/') + '/'
            url = store_url + f"{asset_id}.{data_fmt}"

            if download_file(url, dest):
                success_count += 1
                log_callback(f"  ⬇️ [{idx}/{total_assets}] 下载成功 - {filename}")
            else:
                fail_count += 1
                log_callback(f"  ⚠️ [{idx}/{total_assets}] 下载失败 - {filename}")

            if progress_callback:
                progress_callback(success_count, total_assets)

        log_callback(f"\n📊 素材下载完成：成功 {success_count} 个，失败 {fail_count} 个")
        if fail_count > 0:
            log_callback("  部分素材缺失可能影响作品")

        log_callback(f"🗜️ 正在生成 Scratch 作品文件：{output_sb3_path}")
        with zipfile.ZipFile(output_sb3_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                zf.write(file_path, arcname=file)

        log_callback(f"\n🎉 作品已成功保存至：{os.path.abspath(output_sb3_path)}")

    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        log_callback("📂 临时文件夹已清理")

# ------------------------------------------------------------
# GUI 主类
# ------------------------------------------------------------
class KadaDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"难猜的卡搭 {VERSION}")
        self.root.geometry("720x620")
        self.root.minsize(400, 400)

        # 样式
        style = ttk.Style()
        style.theme_use('vista' if sys.platform == 'win32' else 'clam')

        # ---------- 顶部菜单栏 ----------
        self.create_menu()

        # ---------- 主 Notebook（标签页） ----------
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # 创建两个标签页
        self.create_web_tab()
        self.create_local_tab()

        # ---------- 公共日志区域（带清空按钮）----------
        log_frame = ttk.LabelFrame(root, text="📋 运行日志")
        log_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # 日志工具栏（右侧清空按钮）
        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.pack(fill=X, padx=5, pady=2)
        ttk.Label(log_toolbar, text="实时输出：").pack(side=LEFT)
        ttk.Button(log_toolbar, text="🧹 清空日志", command=self.clear_log).pack(side=RIGHT)

        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=WORD, height=12,
                                                  font=("Consolas", 9))
        self.log_area.pack(fill=BOTH, expand=False, padx=5, pady=5)
        self.log_area.config(state=NORMAL)

        # ---------- 进度条 ----------
        progress_frame = ttk.Frame(root)
        progress_frame.pack(fill=X, padx=10, pady=5)
        ttk.Label(progress_frame, text="下载进度：").pack(side=LEFT)
        self.progress = ttk.Progressbar(progress_frame, orient=HORIZONTAL,
                                        length=500, mode='determinate')
        self.progress.pack(side=LEFT, padx=5)
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=LEFT, expand=False, padx=5)

        # ---------- 状态栏（动态操作提示）----------
        self.status_var = StringVar()
        self.status_var.set("就绪 | 请在操作栏中输入卡搭作品展示页地址并开始下载")
        status_bar = ttk.Label(root, textvariable=self.status_var,
                               relief=SUNKEN, anchor=W, font=("微软雅黑", 9))
        status_bar.pack(fill=X, side=BOTTOM, ipady=2)

        # 线程队列（用于线程安全更新UI）
        self.queue = Queue()
        self.poll_queue()

        # 记录最新生成的作品路径，用于成功弹窗
        self.last_output_path = None

    # --------------------------------------------------------
    # 创建菜单栏
    # --------------------------------------------------------
    def create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        # 帮助菜单
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

    # --------------------------------------------------------
    # 关于窗口
    # --------------------------------------------------------
    def show_about(self):
        about_win = Toplevel(self.root)
        about_win.title(f"关于 难猜的卡搭 {VERSION}")
        about_win.geometry("420x300")
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()

        # 标题
        ttk.Label(about_win, text=f"难猜的卡搭 {VERSION}",
                  font=("微软雅黑", 14, "bold")).pack(pady=10)

        # 作者（超链接）
        author_frame = ttk.Frame(about_win)
        author_frame.pack(pady=5)
        ttk.Label(author_frame, text="作者：").pack(side=LEFT)
        for author in AUTHOR_INFO:
            link = Label(author_frame, text=author["name"], fg="blue", cursor="hand2")
            link.pack(side=LEFT, padx=2)
            link.bind("<Button-1>", lambda e, url=author["url"]: webbrowser.open(url))

        # 联系方式
        ttk.Label(about_win, text=CONTACT, wraplength=380, justify=LEFT).pack(pady=5)

        # 版本说明链接
        notes_link = Label(about_win, text="📖 查看版本更新说明",
                           fg="blue", cursor="hand2")
        notes_link.pack(pady=5)
        notes_link.bind("<Button-1>", lambda e: webbrowser.open(VERSION_NOTES_URL))

        # 关闭按钮
        ttk.Button(about_win, text="关闭", command=about_win.destroy).pack(pady=10)

    # --------------------------------------------------------
    # 创建网页下载标签页
    # --------------------------------------------------------
    def create_web_tab(self):
        self.web_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.web_frame, text="🌐 从网页下载")

        # 操作提示
        tip_text = "💡 输入卡搭作品展示页 URL，按回车开始下载；可自定义保存位置"
        ttk.Label(self.web_frame, text=tip_text, foreground="#2c3e50",
                  font=("微软雅黑", 9)).grid(row=0, column=0, columnspan=3,
                                            padx=5, pady=5, sticky=W)

        # URL 输入
        ttk.Label(self.web_frame, text="卡搭作品页面 URL：").grid(
            row=1, column=0, padx=5, pady=10, sticky=W)
        self.url_var = StringVar()
        url_entry = ttk.Entry(self.web_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=1, column=1, padx=5, pady=10, sticky=EW)
        url_entry.bind("<Return>", lambda e: self.start_web_download())  # 回车下载

        self.web_btn = ttk.Button(self.web_frame, text="开始下载",
                                  command=self.start_web_download)
        self.web_btn.grid(row=1, column=2, padx=5, pady=10)

        # 输出文件保存位置（可选）
        ttk.Label(self.web_frame, text="保存位置（可不填）：").grid(
            row=2, column=0, padx=5, pady=5, sticky=W)
        self.web_output_var = StringVar()
        web_output_entry = ttk.Entry(self.web_frame, textvariable=self.web_output_var, width=50)
        web_output_entry.grid(row=2, column=1, padx=5, pady=5, sticky=EW)
        ttk.Button(self.web_frame, text="浏览",
                   command=self.browse_web_output).grid(row=2, column=2, padx=5, pady=5)

        self.web_frame.columnconfigure(1, weight=1)

        # 额外小提示（分散布局）
        ttk.Label(self.web_frame, text="⏎ 回车键直接下载",
                  foreground="gray").grid(row=3, column=1, padx=5, pady=2, sticky=E)

    # --------------------------------------------------------
    # 创建本地转换标签页
    # --------------------------------------------------------
    def create_local_tab(self):
        self.local_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.local_frame, text="📁 从本地 JSON 转换")

        # 操作提示
        tip_text = "💡 选择已有的 project.json 文件，按回车开始转换"
        ttk.Label(self.local_frame, text=tip_text, foreground="#2c3e50",
                  font=("微软雅黑", 9)).grid(row=0, column=0, columnspan=3,
                                            padx=5, pady=5, sticky=W)

        # JSON 文件选择
        ttk.Label(self.local_frame, text="project.json 文件：").grid(
            row=1, column=0, padx=5, pady=10, sticky=W)
        self.json_path_var = StringVar()
        json_entry = ttk.Entry(self.local_frame, textvariable=self.json_path_var, width=60)
        json_entry.grid(row=1, column=1, padx=5, pady=10, sticky=EW)
        json_entry.bind("<Return>", lambda e: self.start_local_convert())  # 回车转换
        ttk.Button(self.local_frame, text="浏览",
                   command=self.browse_json).grid(row=1, column=2, padx=5, pady=10)

        # 输出文件保存位置
        ttk.Label(self.local_frame, text="输出 .sb3 文件：").grid(
            row=2, column=0, padx=5, pady=10, sticky=W)
        self.local_output_var = StringVar()
        local_output_entry = ttk.Entry(self.local_frame, textvariable=self.local_output_var, width=50)
        local_output_entry.grid(row=2, column=1, padx=5, pady=10, sticky=EW)
        ttk.Button(self.local_frame, text="浏览",
                   command=self.browse_local_output).grid(row=2, column=2, padx=5, pady=10)

        self.local_btn = ttk.Button(self.local_frame, text="开始转换",
                                    command=self.start_local_convert)
        self.local_btn.grid(row=3, column=1, pady=10)

        self.local_frame.columnconfigure(1, weight=1)

        # 额外小提示
        ttk.Label(self.local_frame, text="⏎ 回车键直接转换",
                  foreground="gray").grid(row=4, column=1, padx=5, pady=2, sticky=E)

    # --------------------------------------------------------
    # 辅助方法：日志与进度更新（线程安全）
    # --------------------------------------------------------
    def log(self, message):
        """向日志区域添加一行（自动换行、滚动）"""
        self.queue.put(('log', message))

    def set_progress(self, current, total):
        """更新进度条"""
        self.queue.put(('progress', current, total))

    def set_status(self, text):
        """更新状态栏"""
        self.queue.put(('status', text))

    def enable_buttons(self, enable=True):
        """启用/禁用所有操作按钮"""
        state = NORMAL if enable else DISABLED
        self.queue.put(('button_state', self.web_btn, state))
        self.queue.put(('button_state', self.local_btn, state))

    def clear_log(self):
        """清空日志区域"""
        self.log_area.delete(1.0, END)

    def poll_queue(self):
        """每隔100ms检查队列，更新UI"""
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == 'log':
                    self.log_area.insert(END, msg[1] + "\n")
                    self.log_area.see(END)
                elif msg[0] == 'progress':
                    _, cur, total = msg
                    percent = int(cur * 100 / total) if total > 0 else 0
                    self.progress['value'] = percent
                    self.progress_label['text'] = f"{percent}%"
                elif msg[0] == 'status':
                    self.status_var.set(msg[1])
                elif msg[0] == 'button_state':
                    _, btn, state = msg
                    btn.config(state=state)
        except:
            pass
        self.root.after(100, self.poll_queue)

    # --------------------------------------------------------
    # 文件浏览回调
    # --------------------------------------------------------
    def browse_json(self):
        path = filedialog.askopenfilename(
            title="选择 project.json 文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            self.json_path_var.set(path)
            # 自动生成输出文件名
            default_output = os.path.splitext(path)[0] + ".sb3"
            self.local_output_var.set(default_output)

    def browse_local_output(self):
        path = filedialog.asksaveasfilename(
            title="保存 .sb3 文件",
            defaultextension=".sb3",
            filetypes=[("Scratch 3 作品", "*.sb3"), ("All files", "*.*")]
        )
        if path:
            self.local_output_var.set(path)

    def browse_web_output(self):
        path = filedialog.asksaveasfilename(
            title="保存 .sb3 文件",
            defaultextension=".sb3",
            filetypes=[("Scratch 3 作品", "*.sb3"), ("All files", "*.*")]
        )
        if path:
            self.web_output_var.set(path)

    # --------------------------------------------------------
    # 成功弹窗（自定义）
    # --------------------------------------------------------
    def show_success_dialog(self, file_path):
        """下载成功后显示自定义对话框，包含打开作品和显示位置按钮"""
        self.last_output_path = file_path
        dialog = Toplevel(self.root)
        dialog.title("下载完成")
        dialog.geometry("380x150")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        ttk.Label(dialog, text="✅ 作品已成功生成！",
                  font=("微软雅黑", 11, "bold")).pack(pady=10)
        ttk.Label(dialog, text=f"保存位置：{os.path.basename(file_path)}",
                  wraplength=350).pack(pady=5)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="📂 打开作品",
                   command=lambda: self.open_file(file_path)).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="📍 显示位置",
                   command=lambda: self.reveal_file(file_path)).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭",
                   command=dialog.destroy).pack(side=LEFT, padx=5)

    # --------------------------------------------------------
    # 跨平台文件操作
    # --------------------------------------------------------
    def open_file(self, path):
        """打开作品文件"""
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("打开失败", f"无法打开文件：{e}")

    def reveal_file(self, path):
        """在文件管理器中定位文件"""
        try:
            if sys.platform == 'win32':
                os.system(f'explorer.exe /select,"{os.path.abspath(path)}"')
            elif sys.platform == 'darwin':
                os.system(f'open -R "{path}"')
            else:
                parent = os.path.dirname(os.path.abspath(path))
                self.open_file(parent)
        except Exception as e:
            messagebox.showerror("定位失败", f"无法定位文件：{e}")

    # --------------------------------------------------------
    # 任务启动（子线程）
    # --------------------------------------------------------
    def start_web_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("输入错误", "请输入卡搭作品页面 URL")
            return

        # 禁用按钮
        self.enable_buttons(False)
        self.set_status("正在获取作品信息...")
        self.progress['value'] = 0
        self.progress_label['text'] = "0%"
        self.clear_log()

        # 启动线程
        thread = threading.Thread(target=self._web_download_task, args=(url,), daemon=True)
        thread.start()

    def _web_download_task(self, raw_url):
        try:
            page_url = modify_kada_url(raw_url)
            self.log(f"🌐 处理后的页面地址：{page_url}")
            project_json_url, project_name, author_name = extract_project_info_from_kada_page(page_url)
            self.log(f"🔗 作品名称：{project_name}  作者：{author_name}")
            self.log(f"🔗 project.json 地址：{project_json_url}")

            project_data = download_json_from_url(project_json_url)

            # 确定输出路径
            output_path = self.web_output_var.get().strip()
            if not output_path:
                safe_name = re.sub(r'[\\/*?:"<>|]', "_", project_name)
                timestamp = datetime.now().strftime("%H%M%S")
                output_path = f"{safe_name}-{timestamp}.sb3"
            else:
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            self.log(f"💾 输出文件：{output_path}")
            self.set_status("正在下载素材并打包...")

            build_sb3_from_project_data(
                project_data,
                output_path,
                log_callback=self.log,
                progress_callback=self.set_progress
            )

            self.set_status("下载完成！")
            self.log("✅ 所有任务已结束")

            # 成功弹窗（必须在主线程调用）
            self.queue.put(('success_dialog', output_path))

        except Exception as e:
            self.log(f"❌ 错误：{str(e)}")
            self.set_status("下载失败")
            import traceback
            self.log(traceback.format_exc())
            # 失败弹窗
            self.queue.put(('error_dialog', f"下载失败：{str(e)}"))
        finally:
            self.enable_buttons(True)

    def start_local_convert(self):
        json_path = self.json_path_var.get().strip()
        if not json_path or not os.path.isfile(json_path):
            messagebox.showwarning("输入错误", "请选择有效的 project.json 文件")
            return

        output_path = self.local_output_var.get().strip()
        if not output_path:
            base = os.path.splitext(json_path)[0]
            output_path = base + ".sb3"

        # 禁用按钮
        self.enable_buttons(False)
        self.set_status("正在处理本地文件...")
        self.progress['value'] = 0
        self.progress_label['text'] = "0%"
        self.clear_log()

        thread = threading.Thread(target=self._local_convert_task,
                                  args=(json_path, output_path), daemon=True)
        thread.start()

    def _local_convert_task(self, json_path, output_path):
        try:
            self.log(f"📂 读取本地 JSON：{json_path}")
            with open(json_path, 'r', encoding='utf-8-sig') as f:
                project_data = json.load(f)
            self.log("✅ JSON 解析成功")

            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

            build_sb3_from_project_data(
                project_data,
                output_path,
                log_callback=self.log,
                progress_callback=self.set_progress
            )

            self.set_status("转换完成！")
            self.log("✅ 所有任务已结束")
            self.queue.put(('success_dialog', output_path))

        except Exception as e:
            self.log(f"❌ 错误：{str(e)}")
            self.set_status("转换失败")
            import traceback
            self.log(traceback.format_exc())
            self.queue.put(('error_dialog', f"转换失败：{str(e)}"))
        finally:
            self.enable_buttons(True)

    # --------------------------------------------------------
    # 扩展队列消息处理（支持弹窗）
    # --------------------------------------------------------
    def poll_queue(self):
        """增强版队列轮询，支持成功/失败弹窗"""
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == 'log':
                    self.log_area.insert(END, msg[1] + "\n")
                    self.log_area.see(END)
                elif msg[0] == 'progress':
                    _, cur, total = msg
                    percent = int(cur * 100 / total) if total > 0 else 0
                    self.progress['value'] = percent
                    self.progress_label['text'] = f"{percent}%"
                elif msg[0] == 'status':
                    self.status_var.set(msg[1])
                elif msg[0] == 'button_state':
                    _, btn, state = msg
                    btn.config(state=state)
                elif msg[0] == 'success_dialog':
                    self.show_success_dialog(msg[1])
                elif msg[0] == 'error_dialog':
                    messagebox.showerror("操作失败", msg[1])
        except:
            pass
        self.root.after(100, self.poll_queue)

# ------------------------------------------------------------
# 程序入口
# ------------------------------------------------------------
if __name__ == "__main__":
    root = Tk()
    app = KadaDownloaderGUI(root)
    root.mainloop()
    sys.exit(0)