from pydantic import BaseModel, Field 
from typing import Optional, List 
from datetime import datetime 
 
class CommentResponse(BaseModel): 
    id: int 
    content: str 
    user_id: int 
    created_at: datetime 
 
    class Config: 
        from_attributes = True 

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
 
class TicketCreate(BaseModel): 
    title: str = Field(..., max_length=100) 
    description: str = Field(..., min_length=1, max_length=5000)
    department_name: str = Field(..., description="Departman adı")
    priority: str = Field("Low", pattern="^(Low|Medium|High)$") 
 
class TicketResponse(BaseModel): 
    id: int 
    title: str 
    description: str
    status: str 
    priority: str 
    assigned_department_id: int 
    created_by_user_id: int
    assigned_support_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    comments: List[CommentResponse] = [] 
 
    class Config: 
        from_attributes = True 
 
class CommentCreate(BaseModel): 
    content: str 
