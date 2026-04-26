import logging
from data_collection_pipeline.storage.json_store import JsonStore
from data_collection_pipeline.crawlers.custom_article import CustomArticleCrawler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
store = JsonStore(data_dir="data")
user = store.get_or_create_user(first_name="Test", last_name="Author")
crawler = CustomArticleCrawler( store=store)
url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
crawler.extract(link=url, user=user)
print(f"Articles stored: {len(store.load_articles())}")