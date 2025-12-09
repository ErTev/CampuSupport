from pydantic import BaseModel, Field 
from typing import Optional, List 
from datetime import datetime 


class UserSimpleResponse(BaseModel):
    id: int
    email: str
    role_id: int
    role_name: Optional[str] = None
    
    class Config:
        from_attributes = True


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
    title: Optional[str] = Field(None, max_length=100) 
    description: str = Field(..., min_length=1, max_length=5000)
    department_name: Optional[str] = Field(None, description="Departman adı")
    category: Optional[str] = Field(None, description="(Opsiyonel) Ticket kategorisi")
    priority: Optional[str] = Field("Low", pattern="^(Low|Medium|High)$") 
 
class TicketResponse(BaseModel): 
    id: int 
    title: str 
    description: str
    status: str 
    priority: str 
    category: Optional[str] = None
    assigned_department_id: int 
    created_by_user_id: int
    created_by_user: Optional[UserSimpleResponse] = None
    assigned_support_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    comments: List[CommentResponse] = [] 
 
    class Config: 
        from_attributes = True 


class SuggestRequest(BaseModel):
    title: str = Field(None, max_length=100)
    description: str = Field(..., min_length=1, max_length=5000)



class SuggestResponse(BaseModel):
    suggested_title: Optional[str] = None
    department_options: List[str] = []
    category_options: List[str] = []
    priority_options: List[str] = []
    explanation: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    new_status: str = Field(..., pattern="^(Open|In Progress|Resolved|Closed)$")
    resolution_note: Optional[str] = Field(None, max_length=2000, description="(Opsiyonel) Support tarafından eklenen çözüm notu veya açıklama")


class ReassignSupportRequest(BaseModel):
    new_support_id: int
