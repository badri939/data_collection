from pydantic import BaseModel
from pydantic import Field
from uuid import UUID
from uuid import uuid4

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    


class RawArticleContent (BaseModel):
    title: str | None = None
    description: str | None = None
    language: str | None = None
    main_content: str


    

class RawArticleDocument(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    link: str
    platform: str
    author_id:UUID 
    author_full_name: str 
    content: RawArticleContent
    
    