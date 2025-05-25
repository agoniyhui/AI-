"""
安装和打包脚本 - 用于生成Windows安装包
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# PyInstaller配置文件
SPEC_CONTENT = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/icon.png', 'assets'), ('assets/icon.ico', 'assets')],
    hiddenimports=['win10toast_click'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI科技新闻通知',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI科技新闻通知',
)
"""

# 依赖列表
REQUIREMENTS = """
PyQt6>=6.4.0
feedparser>=6.0.10
win10toast-click>=0.1.2
requests>=2.28.1
"""

# 安装说明
INSTALL_GUIDE = """# AI科技新闻通知软件 - 安装说明

## 系统要求
- Windows 10/11 操作系统
- 至少500MB可用磁盘空间
- 至少2GB内存
- 互联网连接

## 安装方法

### 方法一：使用安装包（推荐）
1. 下载安装包 `AI科技新闻通知_安装包.zip`
2. 解压缩下载的文件
3. 运行解压后的 `setup.exe` 文件
4. 按照安装向导的提示完成安装
5. 安装完成后，可以从开始菜单或桌面快捷方式启动应用

### 方法二：从源代码安装
如果您熟悉Python开发环境，也可以从源代码安装：

1. 确保您的系统已安装Python 3.9或更高版本
2. 下载源代码包 `ai_news_notifier_source.zip`
3. 解压缩下载的文件
4. 打开命令提示符，进入解压后的目录
5. 运行以下命令安装依赖：
   ```
   pip install -r requirements.txt
   ```
6. 运行以下命令启动应用：
   ```
   python src/main.py
   ```

## 开机自启动设置
1. 启动应用后，点击工具栏中的"设置"按钮
2. 在设置对话框中，勾选"开机自启动"选项
3. 点击"确定"保存设置

## 卸载方法
1. 在Windows控制面板中打开"程序和功能"
2. 找到"AI科技新闻通知"程序
3. 右键点击并选择"卸载"
4. 按照卸载向导的提示完成卸载

## 常见问题

### 问题：应用无法启动
- 确保您的系统满足最低系统要求
- 尝试以管理员身份运行应用
- 检查是否安装了所有必要的依赖

### 问题：没有收到通知
- 确保Windows通知功能已启用
- 在应用设置中确认已启用通知
- 检查您的互联网连接是否正常

### 问题：自动刷新不工作
- 确保应用正在后台运行（检查系统托盘图标）
- 在设置中确认已设置正确的刷新间隔
- 检查您的互联网连接是否正常

## 技术支持
如有任何问题或需要技术支持，请联系开发者。
"""

# 用户手册
USER_MANUAL = """# AI科技新闻通知软件 - 用户手册

## 软件介绍
AI科技新闻通知是一款专为科技爱好者设计的Windows桌面应用，它可以自动获取全球最先进的AI技术和科技新闻，并以Windows通知的形式推送给用户。软件界面简约，操作便捷，支持历史记录查看和自定义设置。

## 主要功能
- 获取全球最新AI和科技领域新闻
- 以Windows通知形式推送新闻
- 保存历史推送记录
- 支持手动刷新获取最新新闻
- 可自定义刷新频率和通知设置
- 支持开机自启动

## 界面说明

### 主界面
主界面分为以下几个部分：
- 工具栏：包含刷新和设置按钮
- 标签页：包含"最新新闻"和"历史记录"两个标签
- 状态栏：显示当前软件状态

### 系统托盘
软件可以最小化到系统托盘，右键点击托盘图标可以：
- 显示/隐藏主窗口
- 刷新新闻
- 退出应用

## 使用方法

### 获取新闻
- 自动获取：软件会根据设置的刷新间隔自动获取最新新闻
- 手动获取：点击工具栏中的"刷新"按钮手动获取最新新闻

### 查看新闻
- 通知：新闻会以Windows通知的形式推送
- 列表：在主界面的"最新新闻"标签中查看最新获取的新闻
- 历史记录：在"历史记录"标签中查看所有历史新闻

### 阅读新闻
- 点击通知：直接打开浏览器访问新闻原文
- 双击列表项：在主界面中双击新闻条目，打开浏览器访问新闻原文

### 自定义设置
点击工具栏中的"设置"按钮，可以自定义以下选项：
- 启用/禁用通知
- 设置自动刷新间隔（1-60分钟）
- 设置开机自启动
- 设置启动时最小化到托盘

## 快捷操作
- 关闭窗口：应用会最小化到系统托盘而不是退出
- 完全退出：右键点击系统托盘图标，选择"退出"
- 快速刷新：右键点击系统托盘图标，选择"刷新新闻"

## 技巧和建议
- 将应用设置为开机自启动，确保不会错过任何重要新闻
- 设置合适的刷新间隔，过于频繁的刷新可能会影响系统性能
- 已读的新闻会以灰色显示，方便区分
- 通过系统托盘操作可以减少对桌面的干扰

## 故障排除
- 如果没有收到通知，请检查Windows通知设置和应用通知设置
- 如果新闻无法更新，请检查网络连接
- 如果应用无响应，尝试重启应用

## 隐私说明
本应用仅获取公开的新闻信息，不会收集任何个人数据。所有数据都存储在本地，不会上传到任何服务器。
"""

def create_ico_from_png():
    """从PNG创建ICO文件"""
    try:
        from PIL import Image
        png_path = os.path.join('assets', 'icon.png')
        ico_path = os.path.join('assets', 'icon.ico')
        
        if os.path.exists(png_path) and not os.path.exists(ico_path):
            img = Image.open(png_path)
            # 创建多种尺寸的图标
            icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
            img.save(ico_path, sizes=icon_sizes)
            print(f"已从PNG创建ICO文件: {ico_path}")
        else:
            print("PNG文件不存在或ICO文件已存在")
    except ImportError:
        print("未安装PIL库，无法创建ICO文件")
    except Exception as e:
        print(f"创建ICO文件时出错: {str(e)}")

def create_package_files():
    """创建打包所需的文件"""
    # 创建requirements.txt
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(REQUIREMENTS.strip())
    print("已创建requirements.txt")
    
    # 创建PyInstaller规范文件
    with open('ai_news_notifier.spec', 'w', encoding='utf-8') as f:
        f.write(SPEC_CONTENT.strip())
    print("已创建ai_news_notifier.spec")
    
    # 创建安装说明
    with open('安装说明.md', 'w', encoding='utf-8') as f:
        f.write(INSTALL_GUIDE.strip())
    print("已创建安装说明.md")
    
    # 创建用户手册
    with open('用户手册.md', 'w', encoding='utf-8') as f:
        f.write(USER_MANUAL.strip())
    print("已创建用户手册.md")

def create_source_package():
    """创建源代码包"""
    try:
        # 创建临时目录
        temp_dir = 'temp_source'
        os.makedirs(temp_dir, exist_ok=True)
        
        # 复制源代码
        shutil.copytree('src', os.path.join(temp_dir, 'src'))
        
        # 复制资源
        shutil.copytree('assets', os.path.join(temp_dir, 'assets'))
        
        # 复制文档
        shutil.copy('安装说明.md', temp_dir)
        shutil.copy('用户手册.md', temp_dir)
        shutil.copy('requirements.txt', temp_dir)
        
        # 创建ZIP文件
        shutil.make_archive('ai_news_notifier_source', 'zip', temp_dir)
        print("已创建源代码包: ai_news_notifier_source.zip")
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"创建源代码包时出错: {str(e)}")

def create_executable():
    """创建可执行文件"""
    try:
        # 检查PyInstaller是否已安装
        try:
            import PyInstaller
            print("PyInstaller已安装")
        except ImportError:
            print("正在安装PyInstaller...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        
        # 运行PyInstaller
        print("正在创建可执行文件...")
        subprocess.run(['pyinstaller', 'ai_news_notifier.spec'])
        print("已创建可执行文件")
        
        # 创建安装包ZIP
        shutil.make_archive('AI科技新闻通知_安装包', 'zip', 'dist')
        print("已创建安装包: AI科技新闻通知_安装包.zip")
    except Exception as e:
        print(f"创建可执行文件时出错: {str(e)}")

def main():
    """主函数"""
    print("开始打包AI科技新闻通知软件...")
    
    # 确保assets目录存在
    os.makedirs('assets', exist_ok=True)
    
    # 从PNG创建ICO
    create_ico_from_png()
    
    # 创建打包文件
    create_package_files()
    
    # 创建源代码包
    create_source_package()
    
    # 创建可执行文件
    create_executable()
    
    print("打包完成！")

if __name__ == "__main__":
    main()
