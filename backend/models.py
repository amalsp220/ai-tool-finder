"""SQLAlchemy database models for AI Tool Finder."""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between tools and categories
tool_categories = Table(
    'tool_categories',
    Base.metadata,
    Column('tool_id', Integer, ForeignKey('tools.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)


class Tool(Base):
    """Model for AI tools."""
    __tablename__ = 'tools'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    pricing = Column(String(100), nullable=True)
    rating = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    categories = relationship('Category', secondary=tool_categories, back_populates='tools')
    
    def __repr__(self):
        return f"<Tool(id={self.id}, name='{self.name}', url='{self.url}')>"
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'pricing': self.pricing,
            'rating': self.rating,
            'categories': [cat.to_dict() for cat in self.categories],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Category(Base):
    """Model for tool categories."""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tools = relationship('Tool', secondary=tool_categories, back_populates='categories')
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'tool_count': len(self.tools)
        }


# Virtual table for full-text search
# This will be created separately in database.py using raw SQL
# CREATE VIRTUAL TABLE tools_fts USING fts5(name, description, content='tools', content_rowid='id');
