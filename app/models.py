from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class ReadingListItem(Base):
    __tablename__ = "reading_list_items"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    preview_text = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    processed = Column(Boolean, default=False)
    added_date = Column(DateTime, default=datetime.utcnow)
    processed_date = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "preview_text": self.preview_text,
            "content": self.content,
            "summary": self.summary,
            "processed": self.processed,
            "added_date": self.added_date.isoformat() if self.added_date else None,
            "processed_date": self.processed_date.isoformat() if self.processed_date else None,
        }


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
        }
