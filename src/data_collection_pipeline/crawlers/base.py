from abc import ABC, abstractmethod
from data_collection_pipeline.domain.models import RawArticleDocument

class BaseCrawler(ABC):
    model: type[RawArticleDocument]
    @abstractmethod
    def extract(self,link: str, **kwargs) -> None: ...        