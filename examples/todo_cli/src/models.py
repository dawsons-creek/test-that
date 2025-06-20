"""Todo model and related data structures."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Priority(Enum):
    """Todo priority levels."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"


class Status(Enum):
    """Todo completion status."""
    PENDING = "pending"
    COMPLETED = "completed"


@dataclass
class Todo:
    """A todo item with validation and business logic."""
    
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM
    tags: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: Status = Status.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate todo after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Todo title cannot be empty")
        
        if len(self.title) > 200:
            raise ValueError("Todo title cannot exceed 200 characters")
        
        if self.status == Status.COMPLETED and not self.completed_at:
            self.completed_at = datetime.now()
        
        # Ensure tags are unique and lowercase
        self.tags = list(set(tag.lower().strip() for tag in self.tags if tag.strip()))
    
    def complete(self) -> None:
        """Mark todo as completed."""
        if self.status == Status.COMPLETED:
            raise ValueError("Todo is already completed")
        
        self.status = Status.COMPLETED
        self.completed_at = datetime.now()
    
    def reopen(self) -> None:
        """Reopen a completed todo."""
        if self.status == Status.PENDING:
            raise ValueError("Todo is already pending")
        
        self.status = Status.PENDING
        self.completed_at = None
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the todo."""
        tag = tag.lower().strip()
        if not tag:
            raise ValueError("Tag cannot be empty")
        
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the todo."""
        tag = tag.lower().strip()
        if tag in self.tags:
            self.tags.remove(tag)
    
    def has_tag(self, tag: str) -> bool:
        """Check if todo has a specific tag."""
        return tag.lower().strip() in self.tags
    
    def matches_search(self, query: str) -> bool:
        """Check if todo matches a search query."""
        query = query.lower()
        return (query in self.title.lower() or 
                query in self.description.lower() or
                any(query in tag for tag in self.tags))
    
    def to_dict(self) -> dict:
        """Convert todo to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'tags': self.tags,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Todo':
        """Create todo from dictionary."""
        return cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description', ''),
            priority=Priority(data.get('priority', 'medium')),
            tags=data.get('tags', []),
            status=Status(data.get('status', 'pending')),
            created_at=datetime.fromisoformat(data['created_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        )