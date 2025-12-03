import uuid
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Note:
    id: str
    description: str
    created_at: datetime
    updated_at: datetime


