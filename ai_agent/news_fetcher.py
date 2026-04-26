"""
News Fetcher Module
-------------------
Fetches financial news headlines from multiple sources.
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json


class NewsFetcher:
    """Fetches financial news from multiple APIs."""
    
    def __init__(self, newsapi_key: Optional[str] = None, alpha_vantage_key: Optional[str] = None):
        """
        Initialize news fetcher with API keys.
        
        Args:
            newsapi_key: NewsAPI.org API key (free tier: 100 requests/day)
            alpha_vantage_key: Alpha Vantage API key (free tier: 5 requests/min)
        """
        self.newsapi_key = newsapi_key
        self.alpha_vantage_key = alpha_vantage_key
        self.cache = {}
        self.cache_expiry = 300  # 5 minutes cache
    
    def fetch_newsapi(self, query: str = "stock market india", days: int = 1) -> List[Dict]:
        """
        Fetch news from NewsAPI.org
        
        Args:
            query: Search query (e.g., "TCS", "Nifty 50", "stock market")
            days: Number of days to look back
            
        Returns:
            List of news articles with title, description, source, date
        """
        if not self.newsapi_key:
            print("⚠️ NewsAPI key not configured. Using fallback.")
            return self._get_fallback_news()
        
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "relevancy",
            "language": "en",
            "apiKey": self.newsapi_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get("articles", [])[:10]:  # Limit to 10
                articles.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "source": article.get("source", {}).get("name", "Unknown"),
                    "published_at": article.get("publishedAt", ""),
                    "url": article.get("url", "")
                })
            
            return articles
            
        except Exception as e:
            print(f"❌ NewsAPI error: {e}")
            return self._get_fallback_news()
    
    def fetch_alpha_vantage_news(self, tickers: List[str] = None) -> List[Dict]:
        """
        Fetch news from Alpha Vantage News Sentiment API.
        
        Args:
            tickers: List of stock tickers (e.g., ["TCS.NS", "RELIANCE.NS"])
            
        Returns:
            List of news with sentiment scores
        """
        if not self.alpha_vantage_key:
            print("⚠️ Alpha Vantage key not configured.")
            return []
        
        if tickers is None:
            tickers = ["TCS", "RELIANCE", "INFY"]
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ",".join(tickers),
            "apikey": self.alpha_vantage_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for item in data.get("feed", [])[:10]:
                articles.append({
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "source": item.get("source", "Unknown"),
                    "published_at": item.get("time_published", ""),
                    "overall_sentiment": item.get("overall_sentiment_label", "Neutral"),
                    "sentiment_score": float(item.get("overall_sentiment_score", 0))
                })
            
            return articles
            
        except Exception as e:
            print(f"❌ Alpha Vantage error: {e}")
            return []
    
    def fetch_all_news(self, stock_name: str = "india stock market") -> List[Dict]:
        """
        Fetch news from all available sources.
        
        Args:
            stock_name: Stock or market to search for
            
        Returns:
            Combined list of news articles
        """
        all_news = []
        
        # Try NewsAPI
        newsapi_articles = self.fetch_newsapi(query=stock_name)
        all_news.extend(newsapi_articles)
        
        # Try Alpha Vantage (if available)
        if self.alpha_vantage_key:
            av_articles = self.fetch_alpha_vantage_news()
            all_news.extend(av_articles)
        
        # If no news, use fallback
        if not all_news:
            all_news = self._get_fallback_news()
        
        return all_news
    
    def _get_fallback_news(self) -> List[Dict]:
        """
        Return fallback/mock news for testing when APIs are unavailable.
        """
        return [
            {
                "title": "Indian markets show resilience amid global uncertainty",
                "description": "Nifty 50 and Sensex remain stable as investors await RBI policy.",
                "source": "Economic Times",
                "published_at": datetime.now().isoformat(),
                "sentiment_hint": "neutral"
            },
            {
                "title": "IT stocks rally on strong earnings outlook",
                "description": "TCS, Infosys, and Wipro lead gains in technology sector.",
                "source": "Moneycontrol",
                "published_at": datetime.now().isoformat(),
                "sentiment_hint": "positive"
            },
            {
                "title": "Banking stocks under pressure due to NPA concerns",
                "description": "PSU banks face headwinds as credit quality remains a concern.",
                "source": "Business Standard",
                "published_at": datetime.now().isoformat(),
                "sentiment_hint": "negative"
            }
        ]
    
    def get_headlines_only(self, stock_name: str = "india stock market") -> List[str]:
        """
        Get only headlines (for sentiment analysis).
        
        Returns:
            List of headline strings
        """
        news = self.fetch_all_news(stock_name)
        headlines = []
        
        for article in news:
            title = article.get("title", "")
            if title:
                headlines.append(title)
            
            # Also include description if available
            desc = article.get("description") or article.get("summary", "")
            if desc:
                headlines.append(desc)
        
        return headlines


# Singleton instance for easy access
_fetcher_instance = None

def get_news_fetcher(newsapi_key: str = None, alpha_vantage_key: str = None) -> NewsFetcher:
    """Get or create news fetcher instance."""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = NewsFetcher(newsapi_key, alpha_vantage_key)
    return _fetcher_instance


if __name__ == "__main__":
    # Test the news fetcher
    print("📰 Testing News Fetcher...")
    fetcher = NewsFetcher()
    
    headlines = fetcher.get_headlines_only("TCS stock")
    print(f"\n📰 Found {len(headlines)} headlines:")
    for i, headline in enumerate(headlines[:5], 1):
        print(f"   {i}. {headline[:80]}...")
