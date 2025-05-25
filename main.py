"""
主应用程序 - 集成所有模块，提供用户界面
"""
import sys
import os
import logging
import threading
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import webbrowser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main_app')

# 导入自定义模块
from news_fetcher import NewsFetcher, NewsItem
from data_storage import DataStorage
from notification import NotificationManager

# PyQt6导入
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QListWidget, QListWidgetItem, QTabWidget,
        QSystemTrayIcon, QMenu, QDialog, QCheckBox, QSpinBox, QFormLayout,
        QGroupBox, QScrollArea, QSplitter, QFrame, QToolBar, QStatusBar,
        QMessageBox
    )
    from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal, QUrl
    from PyQt6.QtGui import QIcon, QAction, QFont, QDesktopServices, QColor, QPalette
    GUI_AVAILABLE = True
except ImportError:
    logger.warning("PyQt6库未安装，GUI功能将不可用")
    GUI_AVAILABLE = False


class NewsListItem(QListWidgetItem):
    """自定义列表项，用于显示新闻条目"""
    
    def __init__(self, news_item: NewsItem):
        """初始化新闻列表项
        
        Args:
            news_item: 新闻条目
        """
        super().__init__()
        self.news_item = news_item
        
        # 设置显示文本
        self.setText(f"{news_item.title}")
        
        # 设置工具提示
        self.setToolTip(f"来源: {news_item.source}\n"
                        f"分类: {news_item.category}\n"
                        f"发布时间: {news_item.published_time.strftime('%Y-%m-%d %H:%M')}")
        
        # 设置已读/未读状态的样式
        if news_item.is_read:
            self.setForeground(QColor(120, 120, 120))  # 灰色表示已读
        else:
            self.setForeground(QColor(0, 0, 0))  # 黑色表示未读


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None, storage=None):
        """初始化设置对话框
        
        Args:
            parent: 父窗口
            storage: 数据存储对象
        """
        super().__init__(parent)
        self.storage = storage
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 通知设置组
        notification_group = QGroupBox("通知设置")
        notification_layout = QFormLayout()
        
        # 启用通知选项
        self.enable_notification = QCheckBox()
        self.enable_notification.setChecked(
            self.storage.get_setting("notification_enabled", True) if self.storage else True
        )
        notification_layout.addRow("启用通知:", self.enable_notification)
        
        # 自动刷新间隔
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(1, 60)
        self.refresh_interval.setValue(
            self.storage.get_setting("refresh_interval", 15) if self.storage else 15
        )
        self.refresh_interval.setSuffix(" 分钟")
        notification_layout.addRow("自动刷新间隔:", self.refresh_interval)
        
        notification_group.setLayout(notification_layout)
        layout.addWidget(notification_group)
        
        # 启动设置组
        startup_group = QGroupBox("启动设置")
        startup_layout = QFormLayout()
        
        # 开机自启动选项
        self.auto_start = QCheckBox()
        self.auto_start.setChecked(
            self.storage.get_setting("auto_start", False) if self.storage else False
        )
        startup_layout.addRow("开机自启动:", self.auto_start)
        
        # 启动时最小化到托盘
        self.start_minimized = QCheckBox()
        self.start_minimized.setChecked(
            self.storage.get_setting("start_minimized", True) if self.storage else True
        )
        startup_layout.addRow("启动时最小化到托盘:", self.start_minimized)
        
        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)
        
        # 确定和取消按钮
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_settings(self) -> Dict[str, Any]:
        """获取设置值
        
        Returns:
            设置字典
        """
        return {
            "notification_enabled": self.enable_notification.isChecked(),
            "refresh_interval": self.refresh_interval.value(),
            "auto_start": self.auto_start.isChecked(),
            "start_minimized": self.start_minimized.isChecked()
        }


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 初始化组件
        self.fetcher = NewsFetcher()
        
        # 使用用户文档目录下的数据库
        app_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "AINewsNotifier")
        os.makedirs(app_data_dir, exist_ok=True)
        db_path = os.path.join(app_data_dir, "news_data.db")
        self.storage = DataStorage(db_path)
        
        self.notification_manager = NotificationManager()
        
        # 设置窗口属性
        self.setWindowTitle("AI科技新闻通知")
        self.setMinimumSize(800, 600)
        
        # 创建系统托盘图标
        self.setup_tray_icon()
        
        # 创建UI
        self.setup_ui()
        
        # 加载设置
        self.load_settings()
        
        # 启动自动刷新定时器
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh_news)
        self.start_refresh_timer()
        
        # 初始加载新闻
        self.refresh_news()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建工具栏
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)
        
        # 刷新按钮
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.refresh_news)
        toolbar.addAction(refresh_action)
        
        # 设置按钮
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
        
        # 创建标签页
        self.tabs = QTabWidget()
        
        # 最新新闻标签页
        self.latest_tab = QWidget()
        latest_layout = QVBoxLayout(self.latest_tab)
        
        self.latest_list = QListWidget()
        self.latest_list.itemDoubleClicked.connect(self.on_news_item_clicked)
        latest_layout.addWidget(self.latest_list)
        
        self.tabs.addTab(self.latest_tab, "最新新闻")
        
        # 历史记录标签页
        self.history_tab = QWidget()
        history_layout = QVBoxLayout(self.history_tab)
        
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.on_news_item_clicked)
        history_layout.addWidget(self.history_list)
        
        self.tabs.addTab(self.history_tab, "历史记录")
        
        # 将标签页添加到主布局
        main_layout.addWidget(self.tabs)
        
        # 创建状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("准备就绪")
    
    def setup_tray_icon(self):
        """设置系统托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置图标
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(app_dir, "assets", "icon.ico")
        
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
            self.setWindowIcon(QIcon(icon_path))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 显示/隐藏主窗口
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        # 刷新新闻
        refresh_action = QAction("刷新新闻", self)
        refresh_action.triggered.connect(self.refresh_news)
        tray_menu.addAction(refresh_action)
        
        # 分隔线
        tray_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close_application)
        tray_menu.addAction(exit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 托盘图标点击事件
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
    
    def on_tray_icon_activated(self, reason):
        """托盘图标点击事件处理
        
        Args:
            reason: 激活原因
        """
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击托盘图标，切换窗口显示状态
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def closeEvent(self, event):
        """窗口关闭事件处理
        
        Args:
            event: 关闭事件
        """
        # 隐藏窗口而不是关闭应用
        event.ignore()
        self.hide()
        
        # 显示提示消息
        self.tray_icon.showMessage(
            "AI科技新闻通知",
            "应用程序仍在后台运行。要完全退出，请右键点击托盘图标并选择"退出"。",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    
    def close_application(self):
        """完全关闭应用程序"""
        # 保存设置
        self.save_settings()
        
        # 停止定时器
        self.refresh_timer.stop()
        
        # 退出应用
        QApplication.quit()
    
    def load_settings(self):
        """加载设置"""
        # 加载通知设置
        self.notification_enabled = self.storage.get_setting("notification_enabled", True)
        
        # 加载刷新间隔
        self.refresh_interval = self.storage.get_setting("refresh_interval", 15)
        
        # 加载启动设置
        self.auto_start = self.storage.get_setting("auto_start", False)
        self.start_minimized = self.storage.get_setting("start_minimized", True)
        
        # 如果设置为启动时最小化，则隐藏窗口
        if self.start_minimized:
            self.hide()
    
    def save_settings(self):
        """保存设置"""
        # 保存通知设置
        self.storage.save_setting("notification_enabled", self.notification_enabled)
        
        # 保存刷新间隔
        self.storage.save_setting("refresh_interval", self.refresh_interval)
        
        # 保存启动设置
        self.storage.save_setting("auto_start", self.auto_start)
        self.storage.save_setting("start_minimized", self.start_minimized)
        
        # 如果启用了自启动，设置注册表
        self.set_auto_start(self.auto_start)
    
    def set_auto_start(self, enabled: bool):
        """设置开机自启动
        
        Args:
            enabled: 是否启用
        """
        # 在Windows上，通过注册表设置开机自启动
        # 注意：这需要管理员权限，或者使用其他方法如任务计划
        if sys.platform == "win32":
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE
                )
                
                if enabled:
                    # 获取应用程序路径
                    app_path = sys.executable
                    winreg.SetValueEx(key, "AINewsNotifier", 0, winreg.REG_SZ, app_path)
                else:
                    try:
                        winreg.DeleteValue(key, "AINewsNotifier")
                    except FileNotFoundError:
                        pass
                
                winreg.CloseKey(key)
                logger.info(f"设置开机自启动: {enabled}")
            except Exception as e:
                logger.error(f"设置开机自启动失败: {str(e)}")
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self, self.storage)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 获取设置
            settings = dialog.get_settings()
            
            # 更新设置
            self.notification_enabled = settings["notification_enabled"]
            self.refresh_interval = settings["refresh_interval"]
            self.auto_start = settings["auto_start"]
            self.start_minimized = settings["start_minimized"]
            
            # 保存设置
            self.save_settings()
            
            # 重启定时器
            self.start_refresh_timer()
    
    def start_refresh_timer(self):
        """启动自动刷新定时器"""
        # 停止现有定时器
        self.refresh_timer.stop()
        
        # 如果启用了自动刷新，启动定时器
        if self.refresh_interval > 0:
            # 转换为毫秒
            interval_ms = self.refresh_interval * 60 * 1000
            self.refresh_timer.start(interval_ms)
            logger.info(f"启动自动刷新定时器，间隔: {self.refresh_interval}分钟")
    
    def auto_refresh_news(self):
        """自动刷新新闻"""
        logger.info("自动刷新新闻...")
        self.refresh_news(show_notification=self.notification_enabled)
    
    def refresh_news(self, show_notification: bool = False):
        """刷新新闻
        
        Args:
            show_notification: 是否显示通知
        """
        self.statusBar.showMessage("正在获取最新新闻...")
        
        # 在后台线程中获取新闻
        threading.Thread(target=self._fetch_news_thread, args=(show_notification,), daemon=True).start()
    
    def _fetch_news_thread(self, show_notification: bool):
        """后台线程获取新闻
        
        Args:
            show_notification: 是否显示通知
        """
        try:
            # 获取新闻
            news_items = self.fetcher.fetch_all_news()
            
            # 保存到数据库
            saved_count = self.storage.save_news_items(news_items)
            
            # 在主线程中更新UI
            QApplication.instance().postEvent(
                self,
                NewsRefreshEvent(saved_count, show_notification)
            )
        except Exception as e:
            logger.error(f"获取新闻失败: {str(e)}")
            
            # 在主线程中更新状态
            QApplication.instance().postEvent(
                self,
                NewsRefreshErrorEvent(str(e))
            )
    
    def update_news_lists(self):
        """更新新闻列表"""
        # 清空列表
        self.latest_list.clear()
        self.history_list.clear()
        
        # 获取最新新闻
        latest_news = self.storage.get_latest_news(20)
        
        # 更新最新新闻列表
        for news_item in latest_news:
            list_item = NewsListItem(news_item)
            self.latest_list.addItem(list_item)
        
        # 获取所有新闻作为历史记录
        all_news = self.storage.get_latest_news(100)
        
        # 更新历史记录列表
        for news_item in all_news:
            list_item = NewsListItem(news_item)
            self.history_list.addItem(list_item)
    
    def on_news_item_clicked(self, item):
        """新闻条目点击事件处理
        
        Args:
            item: 点击的列表项
        """
        # 获取新闻条目
        news_item = item.news_item
        
        # 打开浏览器访问新闻链接
        webbrowser.open(news_item.link)
        
        # 标记为已读
        self.storage.mark_as_read(news_item.id)
        
        # 更新列表项样式
        item.setForeground(QColor(120, 120, 120))
    
    def show_notifications(self, news_items: List[NewsItem]):
        """显示新闻通知
        
        Args:
            news_items: 新闻条目列表
        """
        if not self.notification_enabled or not news_items:
            return
        
        # 最多显示3条通知
        items_to_show = news_items[:3]
        
        # 显示通知
        self.notification_manager.show_multiple_news_notifications(items_to_show)
    
    def event(self, event):
        """事件处理
        
        Args:
            event: 事件对象
            
        Returns:
            是否处理了事件
        """
        if isinstance(event, NewsRefreshEvent):
            # 更新状态栏
            if event.saved_count > 0:
                self.statusBar.showMessage(f"获取到{event.saved_count}条新闻")
                
                # 如果有新
(Content truncated due to size limit. Use line ranges to read in chunks)