"""
数据存储模块 - 负责将新闻数据和用户设置保存到本地数据库
"""
import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# 导入NewsItem类
from src.news_fetcher import NewsItem

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_storage')

class DataStorage:
    """数据存储类，负责管理本地SQLite数据库"""
    
    def __init__(self, db_path: str = None):
        """初始化数据存储对象
        
        Args:
            db_path: 数据库文件路径，如果为None则使用默认路径
        """
        if db_path is None:
            # 默认保存在用户文档目录下
            app_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "AINewsNotifier")
            os.makedirs(app_data_dir, exist_ok=True)
            db_path = os.path.join(app_data_dir, "news_data.db")
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建新闻表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_items (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                source TEXT NOT NULL,
                published_time TEXT NOT NULL,
                category TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0
            )
            ''')
            
            # 创建设置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            ''')
            
            # 创建新闻源表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT NOT NULL,
                is_enabled INTEGER NOT NULL DEFAULT 1
            )
            ''')
            
            conn.commit()
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def save_news_items(self, items: List[NewsItem]) -> int:
        """保存新闻条目到数据库
        
        Args:
            items: 新闻条目列表
            
        Returns:
            保存成功的条目数量
        """
        if not items:
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            for item in items:
                try:
                    # 检查是否已存在
                    cursor.execute("SELECT id FROM news_items WHERE title = ?", (item.title,))
                    if cursor.fetchone() is not None:
                        continue
                    
                    # 插入新闻条目
                    cursor.execute('''
                    INSERT INTO news_items (id, title, link, source, published_time, category, is_read)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.id,
                        item.title,
                        item.link,
                        item.source,
                        item.published_time.isoformat(),
                        item.category,
                        1 if item.is_read else 0
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.error(f"保存新闻条目失败: {str(e)}")
            
            conn.commit()
            logger.info(f"成功保存{saved_count}条新闻")
            return saved_count
        except Exception as e:
            logger.error(f"保存新闻条目到数据库失败: {str(e)}")
            return 0
        finally:
            if conn:
                conn.close()
    
    def get_latest_news(self, limit: int = 10) -> List[NewsItem]:
        """获取最新的新闻条目
        
        Args:
            limit: 返回的最大条目数
            
        Returns:
            新闻条目列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, title, link, source, published_time, category, is_read
            FROM news_items
            ORDER BY published_time DESC
            LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            news_items = []
            
            for row in rows:
                item = NewsItem(
                    title=row[1],
                    link=row[2],
                    source=row[3],
                    published_time=datetime.fromisoformat(row[4]),
                    category=row[5],
                    is_read=bool(row[6])
                )
                item.id = row[0]
                news_items.append(item)
            
            logger.info(f"获取了{len(news_items)}条最新新闻")
            return news_items
        except Exception as e:
            logger.error(f"获取最新新闻失败: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_unread_news(self, limit: int = 10) -> List[NewsItem]:
        """获取未读的新闻条目
        
        Args:
            limit: 返回的最大条目数
            
        Returns:
            新闻条目列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, title, link, source, published_time, category, is_read
            FROM news_items
            WHERE is_read = 0
            ORDER BY published_time DESC
            LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            news_items = []
            
            for row in rows:
                item = NewsItem(
                    title=row[1],
                    link=row[2],
                    source=row[3],
                    published_time=datetime.fromisoformat(row[4]),
                    category=row[5],
                    is_read=bool(row[6])
                )
                item.id = row[0]
                news_items.append(item)
            
            logger.info(f"获取了{len(news_items)}条未读新闻")
            return news_items
        except Exception as e:
            logger.error(f"获取未读新闻失败: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def mark_as_read(self, news_id: str) -> bool:
        """将新闻标记为已读
        
        Args:
            news_id: 新闻ID
            
        Returns:
            操作是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE news_items
            SET is_read = 1
            WHERE id = ?
            ''', (news_id,))
            
            conn.commit()
            logger.info(f"将新闻 {news_id} 标记为已读")
            return True
        except Exception as e:
            logger.error(f"标记新闻为已读失败: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def save_setting(self, key: str, value: Any) -> bool:
        """保存设置
        
        Args:
            key: 设置键
            value: 设置值（将被转换为JSON字符串）
            
        Returns:
            操作是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 将值转换为JSON字符串
            value_json = json.dumps(value)
            
            # 检查是否已存在
            cursor.execute("SELECT key FROM settings WHERE key = ?", (key,))
            if cursor.fetchone() is not None:
                # 更新
                cursor.execute('''
                UPDATE settings
                SET value = ?
                WHERE key = ?
                ''', (value_json, key))
            else:
                # 插入
                cursor.execute('''
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ''', (key, value_json))
            
            conn.commit()
            logger.info(f"保存设置 {key}")
            return True
        except Exception as e:
            logger.error(f"保存设置失败: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取设置
        
        Args:
            key: 设置键
            default: 默认值（如果设置不存在）
            
        Returns:
            设置值
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT value
            FROM settings
            WHERE key = ?
            ''', (key,))
            
            row = cursor.fetchone()
            if row is not None:
                # 从JSON字符串转换回Python对象
                return json.loads(row[0])
            else:
                return default
        except Exception as e:
            logger.error(f"获取设置失败: {str(e)}")
            return default
        finally:
            if conn:
                conn.close()


# 测试代码
if __name__ == "__main__":
    from news_fetcher import NewsFetcher
    
    # 使用临时数据库文件进行测试
    test_db_path = "test_news_data.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # 初始化数据存储
    storage = DataStorage(test_db_path)
    
    # 获取新闻
    fetcher = NewsFetcher()
    news = fetcher.fetch_all_news()
    
    # 保存新闻
    saved_count = storage.save_news_items(news)
    print(f"保存了{saved_count}条新闻")
    
    # 获取最新新闻
    latest_news = storage.get_latest_news(5)
    print("\n最新新闻:")
    for item in latest_news:
        print(f"[{item.source}] {item.title}")
    
    # 标记第一条为已读
    if latest_news:
        storage.mark_as_read(latest_news[0].id)
    
    # 保存设置
    storage.save_setting("refresh_interval", 60)
    storage.save_setting("notification_enabled", True)
    
    # 获取设置
    interval = storage.get_setting("refresh_interval", 30)
    enabled = storage.get_setting("notification_enabled", False)
    print(f"\n设置: refresh_interval={interval}, notification_enabled={enabled}")
    
    # 清理测试文件
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
