from data_collection_pipeline.crawlers.base import BaseCrawler
from data_collection_pipeline.domain.models import RawArticleDocument,RawArticleContent,User
from data_collection_pipeline.storage.json_store import JsonStore
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse 
import logging

logger = logging.getLogger(__name__)


class CustomArticleCrawler(BaseCrawler):
    model = RawArticleDocument

    def __init__(self,store:JsonStore):
        self.store = store
    
    def extract(self,link:str,*, user: User, **kwargs) ->None:
        try:
            response = requests.get(link,timeout= 30,headers={"User-Agent": "Mozilla/5.0 (compatible;data_collection_pipeline/0.1"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text,"html.parser")
            title = soup.title.string if soup.title and soup.title.string  else None
            description = soup.find("meta",attrs={"name":"description"})
            description_content = description.get("content")  if description else None
            language=soup.html.get("lang") if soup.html else None
            content_root =soup.find("article") or soup.find("main") or soup.body
            main_content = content_root.get_text(separator = " ",strip=True)
            platform = urlparse(link).netloc.removeprefix("www.")
            article = RawArticleDocument(
                link=link,
                platform=platform,
                author_id = user.id,
                author_full_name = user.full_name,
                content = RawArticleContent(
                    title=title,
                    description=description_content,
                    language=language,
                    main_content=main_content,
                )
            )
            self.store.save_article_if_new(article)
        except requests.RequestException:
            logger.exception("Failed to fetch article from %s", link)
            
