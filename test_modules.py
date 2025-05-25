"""
测试模块 - 用于测试软件各个功能
"""
import os
import sys
import logging
import time
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_module')

# 导入自定义模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.news_fetcher import NewsFetcher, NewsItem
from src.data_storage import DataStorage
from src.notification import NotificationManager

def test_news_fetcher():
    """测试新闻获取模块"""
    logger.info("开始测试新闻获取模块...")
    
    fetcher = NewsFetcher()
    
    # 测试从NewsAPI获取新闻
    news_api_items = fetcher.fetch_from_newsapi()
    logger.info(f"从NewsAPI获取了{len(news_api_items)}条新闻")
    
    # 测试从RSS获取新闻
    rss_items = fetcher.fetch_from_rss()
    logger.info(f"从RSS获取了{len(rss_items)}条新闻")
    
    # 测试获取所有新闻
    all_items = fetcher.fetch_all_news()
    logger.info(f"总共获取了{len(all_items)}条不重复的新闻")
    
    # 打印部分新闻内容
    if all_items:
        logger.info("新闻样例:")
        for i, item in enumerate(all_items[:3]):
            logger.info(f"{i+1}. [{item.source}] {item.title} ({item.category})")
            logger.info(f"   链接: {item.link}")
            logger.info(f"   发布时间: {item.published_time}")
    
    return len(all_items) > 0

def test_data_storage():
    """测试数据存储模块"""
    logger.info("开始测试数据存储模块...")
    
    # 使用临时数据库文件
    test_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_news_data.db")
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    storage = DataStorage(test_db_path)
    
    # 创建测试新闻条目
    test_news = [
        NewsItem(
            title="测试新闻1",
            link="https://example.com/news1",
            source="测试来源1",
            published_time=datetime.now(),
            category="AI"
        ),
        NewsItem(
            title="测试新闻2",
            link="https://example.com/news2",
            source="测试来源2",
            published_time=datetime.now(),
            category="科技"
        )
    ]
    
    # 测试保存新闻
    saved_count = storage.save_news_items(test_news)
    logger.info(f"保存了{saved_count}条新闻")
    
    # 测试获取最新新闻
    latest_news = storage.get_latest_news(5)
    logger.info(f"获取了{len(latest_news)}条最新新闻")
    
    # 测试标记为已读
    if latest_news:
        result = storage.mark_as_read(latest_news[0].id)
        logger.info(f"标记新闻为已读: {'成功' if result else '失败'}")
    
    # 测试获取未读新闻
    unread_news = storage.get_unread_news(5)
    logger.info(f"获取了{len(unread_news)}条未读新闻")
    
    # 测试保存和获取设置
    storage.save_setting("test_key", "test_value")
    value = storage.get_setting("test_key")
    logger.info(f"保存和获取设置: {'成功' if value == 'test_value' else '失败'}")
    
    # 清理测试文件
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    return saved_count == len(test_news) and len(latest_news) > 0

def test_notification():
    """测试通知模块"""
    logger.info("开始测试通知模块...")
    
    notification_manager = NotificationManager()
    
    # 创建测试新闻条目
    test_news = [
        NewsItem(
            title="测试通知1",
            link="https://example.com/news1",
            source="测试来源1",
            published_time=datetime.now(),
            category="AI"
        )
    ]
    
    # 测试显示通知
    result = notification_manager.show_news_notification(test_news[0])
    logger.info(f"显示通知: {'成功' if result else '失败'}")
    
    # 等待一段时间，以便查看通知
    logger.info("等待3秒...")
    time.sleep(3)
    
    return True

def run_all_tests():
    """运行所有测试"""
    logger.info("开始运行所有测试...")
    
    tests = [
        ("新闻获取模块", test_news_fetcher),
        ("数据存储模块", test_data_storage),
        ("通知模块", test_notification)
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"测试{name}...")
        try:
            result = test_func()
            results.append((name, result))
            logger.info(f"{name}测试{'通过' if result else '失败'}")
        except Exception as e:
            logger.error(f"{name}测试出错: {str(e)}")
            results.append((name, False))
    
    # 打印测试结果摘要
    logger.info("\n测试结果摘要:")
    all_passed = True
    for name, result in results:
        logger.info(f"{name}: {'通过' if result else '失败'}")
        if not result:
            all_passed = False
    
    logger.info(f"\n总体结果: {'所有测试通过' if all_passed else '部分测试失败'}")
    return all_passed

if __name__ == "__main__":
    run_all_tests()
