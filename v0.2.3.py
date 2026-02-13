#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
卡搭下载器 V0.2.3
作者：@Copilot (https://www.ccw.site/student/6400af412806993182217040)
       @Deepseek (https://chat.deepseek.com)
版本：2026-02-12
功能：从卡搭（kada.163.com）下载 Scratch 作品并打包为 .sb3 文件
"""

import json
import os
import re
import sys
import tempfile
import time
import zipfile
from datetime import datetime

# ------------------------------------------------------------
# 跨平台工具函数
# ------------------------------------------------------------
def open_file(path):
    """跨平台打开文件或文件夹"""
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':
        os.system(f'open "{path}"')
    else:  # linux
        os.system(f'xdg-open "{path}"')

def reveal_file(path):
    """跨平台在文件管理器中定位文件"""
    if sys.platform == 'win32':
        os.system(f'explorer.exe /select,"{os.path.abspath(path)}"')
    elif sys.platform == 'darwin':
        os.system(f'open -R "{path}"')
    else:  # linux 多数文件管理器不支持直接定位，改为打开父目录
        parent = os.path.dirname(os.path.abspath(path))
        open_file(parent)

def wait_key(message="按 Enter 键继续..."):
    """跨平台等待用户按键"""
    input(message)

# ------------------------------------------------------------
# 模块依赖检查（requests）
# ------------------------------------------------------------
try:
    import requests
except ModuleNotFoundError:
    print("❌ 缺少 requests 模块，请手动安装：")
    print("   pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple/")
    sys.exit(1)

# ------------------------------------------------------------
# 常量定义
# ------------------------------------------------------------
DEFAULT_ASSET_STORE = "https://steam.nosdn.127.net/"   # 备用下载源
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REQUEST_TIMEOUT = 20
DOWNLOAD_RETRIES = 3
RETRY_DELAY = 1

# ------------------------------------------------------------
# URL 规范化处理
# ------------------------------------------------------------
def normalize_url(url, default_protocol="https:"):
    """
    将 URL 补全为以 https:// 开头的完整地址。
    若无法补全（空字符串、仅 '/' 开头等）则返回 None。
    """
    if not url:
        return None
    url = url.strip()
    if url.startswith('https://'):
        return url
    if url.startswith('http://'):
        return 'https://' + url[7:]
    if url.startswith('//'):
        return default_protocol + url
    # 以 '/' 开头的相对路径无法确定域名，视为无效
    if url.startswith('/'):
        return None
    # 其他情况（如直接是域名）补全协议
    return default_protocol + '//' + url

# ------------------------------------------------------------
# JSON 递归处理
# ------------------------------------------------------------
def find_asset_pairs(data):
    """递归查找所有包含 assetId 和 dataFormat 的字典，返回 (assetId, dataFormat) 集合（原始值）"""
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
    """
    递归修改字典/列表，将所有键为 'assetId' 或 'md5ext' 的字符串值中的 '-' 去掉。
    原地修改，无返回值。
    """
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
    """
    递归遍历整个 project.json，收集每个 assetId 对应的有效 assetStore。
    返回字典：{原始 assetId: 规范化后的 assetStore URL}
    """
    mapping = {}
    def _walk(obj):
        if isinstance(obj, dict):
            if 'assetId' in obj and isinstance(obj['assetId'], str):
                asset_id = obj['assetId']
                if 'assetStore' in obj and asset_id not in mapping:
                    store_url = normalize_url(obj['assetStore'])
                    if store_url:  # 仅当返回有效 URL 时才记录
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
    """下载文件，失败重试，成功返回 True"""
    headers = {'User-Agent': USER_AGENT}
    for attempt in range(1, DOWNLOAD_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            if attempt < DOWNLOAD_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                print(f"  ⚠️ 下载失败（已重试 {DOWNLOAD_RETRIES} 次）：{url}\n    错误：{e}")
    return False

def download_json_from_url(url):
    """下载 JSON 文件并解析为 Python 对象，失败时退出程序"""
    try:
        headers = {'User-Agent': USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"❌ 无法下载或解析 project.json：{e}")
        print("   请检查网络连接或链接是否有效。")
        sys.exit(1)

# ------------------------------------------------------------
# 卡搭页面解析
# ------------------------------------------------------------
def extract_project_info_from_kada_page(page_url):
    """
    访问卡搭项目页面，从 <script> 中提取 window.pageData，
    返回 (project_json_url, project_name, author_name)
    """
    print("\n📡 正在分析网页，提取作品信息...")
    try:
        headers = {'User-Agent': USER_AGENT}
        resp = requests.get(page_url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"❌ 无法获取页面：{e}")
        sys.exit(1)

    # 尝试多种方式提取 window.pageData 中的 JSON
    json_str = None
    # 方法1：原代码的括号计数法（保留）
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

    # 方法2：正则表达式匹配（备用）
    if not json_str:
        pattern = r'window\.pageData\s*=\s*({.*?});'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            json_str = match.group(1)

    if not json_str:
        print("❌ 未找到 window.pageData，页面结构可能已变化。")
        sys.exit(1)

    try:
        page_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"❌ 解析 window.pageData 失败：{e}")
        sys.exit(1)

    project_url = page_data.get('projectUrl')
    if not project_url:
        print("❌ window.pageData 中不存在 projectUrl 字段。")
        sys.exit(1)

    project_name = page_data.get('name', '未知作品名')
    author_name = page_data.get('authorName', '未知作者')

    # 规范化 project_url
    project_url = normalize_url(project_url)

    print(f"🔗 作品：{project_name}（作者：{author_name}）")
    print(f"🔗 核心文件地址：{project_url}\n")
    return project_url, project_name, author_name

def modify_kada_url(original_url):
    """将普通项目页转换为 H5 页（便于提取数据）"""
    if original_url.startswith('https://kada.163.com/project/'):
        return original_url.replace(
            'https://kada.163.com/project/',
            'https://kada.163.com/h5/project/',
            1
        )
    return original_url

# ------------------------------------------------------------
# 核心打包流程
# ------------------------------------------------------------
def build_sb3_from_project_data(project_data, output_sb3_path):
    """
    根据已解析的 project_data 字典生成 .sb3 文件
    """
    # 1. 提取原始素材引用（用于下载，URL 需用原始 assetId）
    original_pairs = find_asset_pairs(project_data)
    total_assets = len(original_pairs)
    print(f"📦 共发现 {total_assets} 个素材资源")

    # 2. 构建 assetStore 映射表（使用原始 assetId）
    asset_store_map = collect_asset_store_mapping(project_data)
    print(f"🗂️  其中 {len(asset_store_map)} 个素材拥有专属存储源")

    # 3. 修改 project_data 中的 assetId/md5ext，去除 '-'
    remove_hyphens_from_asset_fields(project_data)

    # 4. 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="kada_downloader_")
    print(f"📁 创建临时文件夹：{temp_dir}")

    try:
        # 5. 写入修改后的 project.json
        json_dest = os.path.join(temp_dir, "project.json")
        with open(json_dest, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, ensure_ascii=False, separators=(',', ':'))
        print("✅ 已写入优化后的 project.json（assetId/md5ext 已去连字符）")

        # 6. 下载所有素材
        success_count = 0
        fail_count = 0
        for idx, (asset_id, data_fmt) in enumerate(original_pairs, start=1):
            clean_asset_id = asset_id.replace('-', '')
            filename = f"{clean_asset_id}.{data_fmt}"
            dest = os.path.join(temp_dir, filename)

            # 获取该素材的专属存储源，若无或无效则使用默认值
            store_url = asset_store_map.get(asset_id)
            if not store_url or not (store_url.startswith('http://') or store_url.startswith('https://')):
                store_url = DEFAULT_ASSET_STORE
            store_url = store_url.rstrip('/') + '/'   # 确保以 / 结尾
            url = store_url + f"{asset_id}.{data_fmt}"

            if download_file(url, dest):
                success_count += 1
                percent = success_count * 100 // total_assets
                print(f"  ⬇️ [{idx}/{total_assets}] 下载成功 ({percent}%) - {filename}")
            else:
                fail_count += 1
                print(f"  ⚠️ [{idx}/{total_assets}] 下载失败 - {filename}")

        print(f"\n📊 素材下载完成：成功 {success_count} 个，失败 {fail_count} 个")
        if fail_count > 0:
            print("  部分素材缺失可能影响作品，建议检查网络或稍后重试。")

        # 7. 打包为 .sb3
        print(f"🗜️ 正在生成 Scratch 作品文件：{output_sb3_path}")
        with zipfile.ZipFile(output_sb3_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                zf.write(file_path, arcname=file)

        print(f"\n🎉 作品已成功保存至：{os.path.abspath(output_sb3_path)}")

    finally:
        # 8. 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("📂 临时文件夹已清理")

# ------------------------------------------------------------
# 主程序入口
# ------------------------------------------------------------
def main():
    print("=" * 60)
    print("卡搭下载器 V0.2.3")
    print("作者：@Copilot  & @Deepseek")
    print("声明：")
    print("  1. 卡搭官网代码随时可能变动，本工具可能失效")
    print("  2. 请勿过于频繁地使用，可能会暂时被服务器封禁")
    print("  3. 运行中可按 Ctrl+C 强制终止")
    print("=" * 60)

    # 模式1：命令行参数 → 本地 project.json 模式
    if len(sys.argv) >= 2:
        json_path = sys.argv[1]
        if not os.path.isfile(json_path):
            print(f"❌ 文件不存在：{json_path}")
            sys.exit(1)

        # 读取 JSON（自动处理 BOM）
        try:
            with open(json_path, 'r', encoding='utf-8-sig') as f:
                project_data = json.load(f)
        except Exception as e:
            print(f"❌ 无法读取或解析 JSON 文件：{e}")
            sys.exit(1)

        # 确定输出文件名
        if len(sys.argv) >= 3:
            output_sb3 = sys.argv[2]
        else:
            base, _ = os.path.splitext(json_path)
            output_sb3 = base + ".sb3"

        build_sb3_from_project_data(project_data, output_sb3)

    # 模式2：无参数 → 交互模式，通过卡搭页面重建
    else:
        print("\n🎮 请输入卡搭作品展示页面 URL（例如：https://kada.163.com/project/xxx.htm，鼠标右键=粘贴）")
        raw_url = input("网页链接: ").strip()
        if not raw_url:
            print("❌ 未输入链接，程序退出")
            sys.exit(1)

        # 转换为 H5 页面链接
        page_url = modify_kada_url(raw_url)

        # 从页面提取作品信息
        project_json_url, project_name, author_name = extract_project_info_from_kada_page(page_url)

        # 下载 project.json
        project_data = download_json_from_url(project_json_url)

        # 生成默认输出文件名
        timestamp = datetime.now().strftime("%H%M%S")
        # 过滤文件名中的非法字符
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", project_name)
        output_sb3 = f"{safe_name}-{timestamp}.sb3"

        # 执行打包
        build_sb3_from_project_data(project_data, output_sb3)

    # 完成后询问是否打开/定位文件
    print("\n📄 是否打开该 Scratch 作品？")
    print("   1 - 直接打开")
    print("   2 - 在文件夹中定位")
    print("   其他 - 不打开")
    choice = input("请选择（1/2/其他）: ").strip()
    if choice == '1':
        open_file(output_sb3)
    elif choice == '2':
        reveal_file(output_sb3)

if __name__ == "__main__":
    main()