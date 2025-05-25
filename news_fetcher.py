"""
新闻获取模块 - 负责从多个来源获取AI和科技相关新闻
"""
import requests
import json
import feedparser
from datetime import datetime
import time
import logging
from typing import List, Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('news_fetcher')

class NewsItem:
    """新闻条目数据结构"""
    def __init__(self, 
                 title: str, 
                 link: str, 
                 source: str, 
                 published_time: datetime,
                 category: str = "AI/科技",
                 is_read: bool = False):
        self.id = f"{source}_{int(time.time())}_{hash(title) % 10000}"
        self.title = title
        self.link = link
        self.source = source
        self.published_time = published_time
        self.category = category
        self.is_read = is_read
    
    def to_dict(self) -> Dict[str, Any]:
        """将对象转换为字典，用于JSON序列化和数据库存储"""
        return {
            'id': self.id,
            'title': self.title,
            'link': self.link,
            'source': self.source,
            'published_time': self.published_time.isoformat(),
            'category': self.category,
            'is_read': self.is_read
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewsItem':
        """从字典创建NewsItem对象"""
        item = cls(
            title=data['title'],
            link=data['link'],
            source=data['source'],
            published_time=datetime.fromisoformat(data['published_time']),
            category=data.get('category', 'AI/科技'),
            is_read=data.get('is_read', False)
        )
        item.id = data['id']
        return item


class NewsFetcher:
    """新闻获取器，负责从多个来源获取新闻"""
    
    def __init__(self):
        # 新闻API密钥和配置
        self.newsapi_key = "YOUR_NEWSAPI_KEY"  # 实际使用时需要替换为真实的API密钥
        
        # 科技和AI相关的RSS订阅源
        self.rss_feeds = [
            {
                "name": "MIT Technology Review",
                "url": "https://www.technologyreview.com/feed/",
                "category": "科技"
            },
            {
                "name": "Wired",
                "url": "https://www.wired.com/feed/rss",
                "category": "科技"
            },
            {
                "name": "AI News",
                "url": "https://artificialintelligence-news.com/feed/",
                "category": "AI"
            },
            {
                "name": "VentureBeat AI",
                "url": "https://venturebeat.com/category/ai/feed/",
                "category": "AI"
            }
        ]
        
        # 关键词过滤器
        self.ai_keywords = [
            "人工智能", "AI", "机器学习", "深度学习", "神经网络", "自然语言处理", 
            "NLP", "计算机视觉", "语音识别", "强化学习", "大语言模型", "LLM",
            "GPT", "BERT", "transformer", "diffusion", "生成式AI", "生成式人工智能"
        ]
        
        self.tech_keywords = [
            "科技", "技术", "创新", "数字化", "量子计算", "区块链", "元宇宙",
            "VR", "AR", "XR", "机器人", "自动驾驶", "物联网", "IoT", "5G", "6G",
            "半导体", "芯片", "云计算", "边缘计算"
        ]
    
    def fetch_from_newsapi(self) -> List[NewsItem]:
        """从NewsAPI获取新闻"""
        logger.info("从NewsAPI获取新闻...")
        
        # 由于实际环境中需要API密钥，这里使用模拟数据
        # 实际使用时应替换为真实API调用
        try:
            # 模拟API响应
            mock_response = {
                "status": "ok",
                "totalResults": 3,
                "articles": [
                    {
                        "source": {"id": "techcrunch", "name": "TechCrunch"},
                        "title": "最新GPT-5模型展示惊人的推理能力",
                        "url": "https://techcrunch.com/2025/05/24/gpt-5-reasoning/",
                        "publishedAt": "2025-05-24T15:30:00Z"
                    },
                    {
                        "source": {"id": "wired", "name": "Wired"},
                        "title": "量子计算突破：首个实用级容错量子处理器问世",
                        "url": "https://www.wired.com/2025/05/quantum-computing-breakthrough/",
                        "publishedAt": "2025-05-24T12:15:00Z"
                    },
                    {
                        "source": {"id": "theverge", "name": "The Verge"},
                        "title": "新型脑机接口技术允许完全瘫痪患者控制机器人手臂",
                        "url": "https://www.theverge.com/2025/5/23/brain-computer-interface",
                        "publishedAt": "2025-05-23T18:45:00Z"
                    }
                ]
            }
            
            news_items = []
            for article in mock_response["articles"]:
                # 确保所有datetime对象都是naive的（不带时区信息）
                dt_str = article["publishedAt"].replace("Z", "")
                dt = datetime.fromisoformat(dt_str)
                
                news_items.append(NewsItem(
                    title=article["title"],
                    link=article["url"],
                    source=article["source"]["name"],
                    published_time=dt,
                    category=self._categorize_by_keywords(article["title"])
                ))
            
            logger.info(f"从NewsAPI获取了{len(news_items)}条新闻")
            return news_items
            
        except Exception as e:
            logger.error(f"从NewsAPI获取新闻失败: {str(e)}")
            return []
    
    def fetch_from_rss(self) -> List[NewsItem]:
        """从RSS订阅源获取新闻"""
        logger.info("从RSS订阅源获取新闻...")
        
        news_items = []
        for feed_info in self.rss_feeds:
            try:
                # 实际环境中应该使用真实的RSS解析
                # 这里使用模拟数据
                if feed_info["name"] == "MIT Technology Review":
                    mock_entries = [
                        {
                            "title": "新型神经形态芯片模拟人脑突触连接",
                            "link": "https://www.technologyreview.com/2025/05/24/neuromorphic-chip/",
                            "published": "Sat, 24 May 2025 10:30:00 GMT"
                        },
                        {
                            "title": "AI辅助药物发现平台缩短新药研发周期",
                            "link": "https://www.technologyreview.com/2025/05/23/ai-drug-discovery/",
                            "published": "Fri, 23 May 2025 14:15:00 GMT"
                        }
                    ]
                elif feed_info["name"] == "AI News":
                    mock_entries = [
                        {
                            "title": "多模态AI系统实现跨领域知识迁移",
                            "link": "https://artificialintelligence-news.com/2025/05/24/multimodal-ai/",
                            "published": "Sat, 24 May 2025 09:45:00 GMT"
                        },
                        {
                            "title": "自监督学习突破：AI模型仅需少量标注数据即可达到SOTA",
                            "link": "https://artificialintelligence-news.com/2025/05/22/self-supervised-learning/",
                            "published": "Thu, 22 May 2025 16:20:00 GMT"
                        }
                    ]
                else:
                    mock_entries = []
                
                for entry in mock_entries:
                    try:
                        # 确保所有datetime对象都是naive的（不带时区信息）
                        published_time = datetime.strptime(entry["published"], "%a, %d %b %Y %H:%M:%S GMT")
                    except ValueError:
                        published_time = datetime.now().replace(tzinfo=None)
                    
                    news_items.append(NewsItem(
                        title=entry["title"],
                        link=entry["link"],
                        source=feed_info["name"],
                        published_time=published_time,
                        category=feed_info["category"]
                    ))
                
            except Exception as e:
                logger.error(f"从{feed_info['name']}获取RSS新闻失败: {str(e)}")
        
        logger.info(f"从RSS订阅源获取了{len(news_items)}条新闻")
        return news_items
    
    def fetch_all_news(self) -> List[NewsItem]:
        """获取所有来源的新闻并合并"""
        all_news = []
        
        # 从各个来源获取新闻
        all_news.extend(self.fetch_from_newsapi())
        all_news.extend(self.fetch_from_rss())
        
        # 按发布时间排序，最新的在前
        all_news.sort(key=lambda x: x.published_time, reverse=True)
        
        # 去重（基于标题）
        unique_titles = set()
        unique_news = []
        
        for item in all_news:
            if item.title not in unique_titles:
                unique_titles.add(item.title)
                unique_news.append(item)
        
        logger.info(f"总共获取了{len(unique_news)}条不重复的新闻")
        return unique_news
    
    def _categorize_by_keywords(self, title: str) -> str:
        """根据标题中的关键词对新闻进行分类"""
        title_lower = title.lower()
        
        # 检查AI关键词
        for keyword in self.ai_keywords:
            if keyword.lower() in title_lower:
                return "AI"
        
        # 检查科技关键词
        for keyword in self.tech_keywords:
            if keyword.lower() in title_lower:
                return "科技"
        
        # 默认分类
        return "AI/科技"


# 测试代码
if __name__ == "__main__":
    fetcher = NewsFetcher()
    news = fetcher.fetch_all_news()
    
    print(f"获取到{len(news)}条新闻:")
    for item in news:
        print(f"[{item.source}] {item.title} ({item.category})")
        print(f"  链接: {item.link}")
        print(f"  发布时间: {item.published_time}")
        print("-" * 50)
