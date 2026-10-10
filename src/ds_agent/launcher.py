# 跨平台启动器。
# 流程：检查 Python -> 建立 .venv -> 安装依赖 -> 引导配置 -> 准备 ds_read.py -> 启动 app.py
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def venv_python(root: Path) -> Path:
    if os.name == 'nt':
        return root / '.venv' / 'Scripts' / 'python.exe'
    return root / '.venv' / 'bin' / 'python'


def check_python() -> bool:
    return sys.version_info >= (3, 10)


def ensure_venv(root: Path) -> Path:
    py = venv_python(root)
    if py.is_file():
        return py
    print('[启动器] 未找到 .venv，正在创建...')
    subprocess.run([sys.executable, '-m', 'venv', str(root / '.venv')], check=True)
    return py


def _has_module(py: Path, name: str) -> bool:
    r = subprocess.run([str(py), '-c', 'import ' + name], capture_output=True)
    return r.returncode == 0


def ensure_deps(py: Path, with_web: bool, with_admin: bool) -> None:
    if not (_has_module(py, 'yaml') and _has_module(py, 'requests')):
        print('[启动器] 安装核心依赖...')
        subprocess.run(
            [str(py), '-m', 'pip', 'install', '-e', '.'],
            cwd=str(project_root()), check=True,
        )
    if with_web and not _has_module(py, 'pyautogui'):
        print('[启动器] 安装网页后端依赖...')
        subprocess.run(
            [str(py), '-m', 'pip', 'install', '-e', '.[web]'],
            cwd=str(project_root()), check=True,
        )
    if with_admin and not _has_module(py, 'fastapi'):
        print('[启动器] 安装管理面板依赖...')
        subprocess.run(
            [str(py), '-m', 'pip', 'install', '-e', '.[admin]'],
            cwd=str(project_root()), check=True,
        )


def ensure_config(py: Path) -> None:
    cfg = project_root() / 'config' / 'config.yaml'
    if cfg.is_file():
        return
    print('[启动器] 未找到 config/config.yaml，进入配置向导...')
    subprocess.run([str(py), '-m', 'ds_agent.config_cli'], cwd=str(project_root()))


def detect_backend() -> str:
    env = os.environ.get('DS_AGENT_BACKEND')
    if env:
        return env.strip().lower()
    cfg = project_root() / 'config' / 'config.yaml'
    if cfg.is_file():
        try:
            import yaml
            data = yaml.safe_load(cfg.read_text(encoding='utf-8')) or {}
            backend = data.get('backend') or {}
            return str(backend.get('type') or 'api').strip().lower()
        except Exception:
            pass
    return 'api'


def _read_config_ds_read_url() -> str:
    # 从 config.yaml 读取 backend.web.ds_read_url 作为内置下载地址。
    cfg = project_root() / 'config' / 'config.yaml'
    if not cfg.is_file():
        return ''
    try:
        import yaml
        data = yaml.safe_load(cfg.read_text(encoding='utf-8')) or {}
        backend = data.get('backend') or {}
        web = backend.get('web') or {}
        return str(web.get('ds_read_url') or '').strip()
    except Exception:
        return ''


def _ds_read_target() -> Path:
    return project_root() / '_internal' / 'ds_read.py'


def prepare_ds_read(url: Optional[str], local_file: Optional[str]) -> Path:
    target = _ds_read_target()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file():
        print('[启动器] 已存在 ds_read.py：' + str(target))
        return target
    if local_file:
        src = Path(local_file).expanduser().resolve()
        if not src.is_file():
            raise SystemExit('[启动器] 本地 ds_read.py 不存在：' + str(src))
        shutil.copy2(src, target)
        print('[启动器] 已复制到 ' + str(target))
        return target
    if url:
        print('[启动器] 正在下载 ds_read.py ...')
        print('[启动器] 来源：' + url)
        try:
            import requests
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            target.write_bytes(r.content)
        except Exception as exc:
            print('[启动器] 下载失败：' + str(exc))
            print('')
            print('[启动器] 常见原因：国内网络无法直接访问 raw.githubusercontent.com')
            print('')
            print('[启动器] 备选方案（任选其一）：')
            print('')
            print('  方案一：使用镜像（在 GitHub raw 地址前加镜像前缀）')
            print('    scripts\\start.bat --with-web --ds-read-url "https://ghproxy.com/https://raw.githubusercontent.com/VZService/SKILL_web-ds-read/main/scripts/ds_read.py"')
            print('    其它可选镜像前缀：https://gh-proxy.com/  https://mirror.ghproxy.com/')
            print('')
            print('  方案二：浏览器手动下载后用本地文件')
            print('    1. 打开 https://github.com/VZService/SKILL_web-ds-read/blob/main/scripts/ds_read.py')
            print('    2. 点击 Raw 按钮，另存为 ds_read.py')
            print('    3. scripts\\start.bat --with-web --ds-read-file "你的路径\\ds_read.py"')
            print('')
            print('  方案三：手动放置到标准位置')
            print('    把 ds_read.py 放到：' + str(target))
            print('    然后 scripts\\start.bat')
            print('')
            print('  方案四：改用 API 后端（推荐，无需下载）')
            print('    .venv\\Scripts\\python.exe -m ds_agent.config_cli')
            print('    选 1，粘贴 DeepSeek API Key')
            print('')
            raise SystemExit('[启动器] 下载失败，请按上方方案重试。')
        print('[启动器] 已保存到 ' + str(target))
        return target
    raise SystemExit(
        '[启动器] 使用网页后端需要 ds_read.py，但未找到。请任选其一：\n'
        '  1. 把 ds_read.py 放到：' + str(target) + '\n'
        '  2. 设置环境变量 DS_AGENT_DS_READ_URL 指向下载地址\n'
        '  3. 在 config/config.yaml 的 backend.web.ds_read_url 填写下载地址\n'
        '  4. 运行时加参数 --ds-read-url 或 --ds-read-file'
    )


def sync_ds_read_path(cfg_path: Path, ds_read: Path) -> None:
    try:
        import yaml
        data = yaml.safe_load(cfg_path.read_text(encoding='utf-8')) or {}
        backend = data.setdefault('backend', {})
        web = backend.setdefault('web', {})
        if web.get('ds_read_script') == str(ds_read):
            return
        web['ds_read_script'] = str(ds_read)
        cfg_path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding='utf-8',
        )
        print('[启动器] 已更新 config/config.yaml 的 backend.web.ds_read_script')
    except Exception as exc:
        print('[启动器] 更新 config.yaml 失败（不影响启动）：' + str(exc))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog='ds_agent.launcher', description='ds-agent 一键启动器')
    parser.add_argument('--audit', action='store_true', help='只打印将发送内容，不实际发送')
    parser.add_argument('--with-web', action='store_true', help='安装网页后端 GUI 依赖')
    parser.add_argument('--with-admin', action='store_true', help='安装管理面板依赖')
    parser.add_argument('--ds-read-url', default='', help='ds_read.py 下载地址')
    parser.add_argument('--ds-read-file', default='', help='本地 ds_read.py 路径')
    parser.add_argument('--skip-setup', action='store_true', help='跳过环境准备')
    args = parser.parse_args(argv)

    print('=' * 60)
    print('  ds-agent 一键启动器')
    print('=' * 60)

    if not check_python():
        print('[启动器] 需要 Python 3.10+，当前 ' + sys.version.split()[0])
        print('[启动器] 下载地址：https://www.python.org/downloads/')
        return 1

    root = project_root()

    if args.skip_setup:
        py = venv_python(root)
        if not py.is_file():
            print('[启动器] 未找到 .venv，无法 --skip-setup')
            return 1
    else:
        py = ensure_venv(root)
        ensure_deps(py, with_web=args.with_web, with_admin=args.with_admin)
        ensure_config(py)

    backend = detect_backend()
    print('[启动器] 后端类型：' + backend)

    if backend == 'web':
        # 优先级：命令行 --ds-read-url > 环境变量 > config.yaml 的 ds_read_url
        url = args.ds_read_url or os.environ.get('DS_AGENT_DS_READ_URL', '') or _read_config_ds_read_url()
        local_file = args.ds_read_file or os.environ.get('DS_AGENT_DS_READ_FILE', '')
        ds_read = prepare_ds_read(url or None, local_file or None)
        cfg_path = root / 'config' / 'config.yaml'
        if cfg_path.is_file():
            sync_ds_read_path(cfg_path, ds_read)

    cmd = [str(py), str(root / 'app.py')]
    if args.audit:
        cmd.append('--audit')
    print('[启动器] 启动主程序...')
    print('-' * 60)
    return subprocess.call(cmd, cwd=str(root))


if __name__ == '__main__':
    raise SystemExit(main())
