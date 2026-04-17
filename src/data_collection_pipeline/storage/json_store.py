from pathlib import Path
import json
from data_collection_pipeline.domain.models import User,RawArticleDocument


class JsonStore:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.users_file_path = self.data_dir / "users.json"
        self.articles_file_path = self.data_dir / "articles.json"


    def load_users(self) -> list[User]:
        if self.users_file_path.exists():
            with self.users_file_path.open('r') as f:
                return [User(**user_data) for user_data in json.load(f)]
        return []
    
    def save_users(self, users: list[User]) -> None:
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)
        with self.users_file_path.open('w') as f:
            json.dump([user.model_dump(mode="json") for user in users], f, indent=4)

    def get_or_create_user(self,first_name:str,last_name:str)->User:
        users = self.load_users()
        for user in users:
            if user.first_name == first_name and user.last_name == last_name:
                return user
        new_user = User(first_name=first_name, last_name=last_name)
        users.append(new_user)
        self.save_users(users)
        return new_user 
    
    def load_articles(self) -> list[RawArticleDocument]:
        if self.articles_file_path.exists():
            with self.articles_file_path.open('r') as f:
                return [RawArticleDocument(**article_data) for article_data in json.load(f)]
        return []
    
    def save_articles(self, articles: list[RawArticleDocument]) -> None:
        if not self.data_dir.exists():
            self.data_dir.mkdir(parents=True)
        with self.articles_file_path.open('w') as f:
            json.dump([article.model_dump(mode="json") for article in articles], f, indent=4)

    def article_exists_by_link(self, link: str) -> bool:
        articles = self.load_articles()
        return any(article.link == link for article in articles)

    def save_article_if_new(self, article: RawArticleDocument) -> bool:
        if self.article_exists_by_link(article.link):
            return False
        articles = self.load_articles()
        articles.append(article)
        self.save_articles(articles)
        return True