"""
通知模块 - 负责将新闻以Windows通知的形式展示给用户
"""
import os
import sys
import logging
import webbrowser
from typing import List, Dict, Any, Optional
from datetime import datetime
import threading
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('notification')

# 导入NewsItem类
from src.news_fetcher import NewsItem

# Windows通知相关导入
# 注意：实际使用时需要安装win10toast_click库
# pip install win10toast-click
try:
    from win10toast_click import ToastNotifier
    NOTIFICATION_AVAILABLE = True
except ImportError:
    logger.warning("win10toast_click库未安装，通知功能将不可用")
    NOTIFICATION_AVAILABLE = False
    
    # 创建一个模拟的ToastNotifier类，用于开发环境
    class ToastNotifier:
        def __init__(self):
            pass
            
        def show_toast(self, title, msg, icon_path, duration, callback_on_click):
            logger.info(f"模拟通知: {title} - {msg}")
            logger.info(f"点击回调: {callback_on_click}")


class NotificationManager:
    """通知管理器，负责显示Windows通知"""
    
    def __init__(self):
        """初始化通知管理器"""
        self.toaster = ToastNotifier() if NOTIFICATION_AVAILABLE else None
        self.icon_path = self._get_icon_path()
        self.active_notifications = {}  # 存储活动通知的回调函数
        
    def _get_icon_path(self) -> str:
        """获取通知图标路径"""
        # 在实际应用中，图标应该放在应用安装目录下
        # 这里使用一个临时路径
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(app_dir, "assets", "icon.ico")
        
        # 如果图标不存在，返回None
        if not os.path.exists(icon_path):
            logger.warning(f"通知图标不存在: {icon_path}")
            return None
        
        return icon_path
    
    def show_news_notification(self, news_item: NewsItem) -> bool:
        """显示新闻通知
        
        Args:
            news_item: 新闻条目
            
        Returns:
            是否成功显示通知
        """
        if not NOTIFICATION_AVAILABLE or self.toaster is None:
            logger.warning("通知功能不可用")
            return False
        
        try:
            # 准备通知内容
            title = f"{news_item.source} - {news_item.category}"
            message = news_item.title
            
            # 创建点击回调函数
            def callback_func():
                self._on_notification_clicked(news_item.link, news_item.id)
            
            # 存储回调函数，防止被垃圾回收
            self.active_notifications[news_item.id] = callback_func
            
            # 显示通知
            threading.Thread(
                target=self.toaster.show_toast,
                args=(title, message, self.icon_path, 5, callback_func),
                daemon=True
            ).start()
            
            logger.info(f"显示新闻通知: {title} - {message}")
            return True
        except Exception as e:
            logger.error(f"显示新闻通知失败: {str(e)}")
            return False
    
    def show_multiple_news_notifications(self, news_items: List[NewsItem], delay: float = 2.0) -> int:
        """显示多条新闻通知，每条之间有延迟
        
        Args:
            news_items: 新闻条目列表
            delay: 每条通知之间的延迟（秒）
            
        Returns:
            成功显示的通知数量
        """
        if not news_items:
            return 0
        
        success_count = 0
        for item in news_items:
            if self.show_news_notification(item):
                success_count += 1
                
                # 等待一段时间再显示下一条通知
                if success_count < len(news_items):
                    time.sleep(delay)
        
        return success_count
    
    def _on_notification_clicked(self, url: str, news_id: str):
        """通知点击事件处理
        
        Args:
            url: 要打开的URL
            news_id: 新闻ID
        """
        try:
            # 打开浏览器访问新闻链接
            webbrowser.open(url)
            logger.info(f"打开新闻链接: {url}")
            
            # 从活动通知中移除
            if news_id in self.active_notifications:
                del self.active_notifications[news_id]
            
            # 在实际应用中，这里应该调用数据存储模块将新闻标记为已读
            # 例如：storage.mark_as_read(news_id)
        except Exception as e:
            logger.error(f"处理通知点击事件失败: {str(e)}")


# 测试代码
if __name__ == "__main__":
    from src.news_fetcher import NewsItem
    from datetime import datetime
    
    # 创建通知管理器
    notification_manager = NotificationManager()
    
    # 创建测试新闻条目
    test_news = [
        NewsItem(
            title="最新GPT-5模型展示惊人的推理能力",
            link="https://example.com/news1",
            source="AI News",
            published_time=datetime.now(),
            category="AI"
        ),
        NewsItem(
            title="量子计算突破：首个实用级容错量子处理器问世",
            link="https://example.com/news2",
            source="Tech Review",
            published_time=datetime.now(),
            category="科技"
        )
    ]
    
    # 显示通知
    notification_manager.show_multiple_news_notifications(test_news)
    
    # 保持程序运行一段时间，以便查看通知
    print("通知已发送，程序将在10秒后退出...")
    time.sleep(10)
