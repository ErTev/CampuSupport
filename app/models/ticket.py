from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, case 
from sqlalchemy.orm import relationship 
from datetime import datetime 
from app.database import Base 
 
class Ticket(Base): 
    __tablename__ = "tickets" 
 
    id = Column(Integer, primary_key=True, index=True) 
    title = Column(String) 
    description = Column(String) 
 
    status = Column(String, default="Open") 
    priority = Column(String, default="Low") 
 
    created_at = Column(DateTime, default=datetime.utcnow) 
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 
 
    created_by_user_id = Column(Integer, ForeignKey("users.id")) 
    assigned_department_id = Column(Integer, ForeignKey("departments.id")) 
    assigned_support_id = Column(Integer, ForeignKey("users.id"), nullable=True) 
 
    creator = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_tickets") 
    assignee = relationship("User", foreign_keys=[assigned_support_id], back_populates="assigned_tickets") 
    assigned_department = relationship("Department", back_populates="tickets") 
 
    comments = relationship("Comment", back_populates="ticket") 
 
class Comment(Base): 
    __tablename__ = "comments" 
 
    id = Column(Integer, primary_key=True, index=True) 
    ticket_id = Column(Integer, ForeignKey("tickets.id")) 
    user_id = Column(Integer, ForeignKey("users.id")) 
    content = Column(String) 
    created_at = Column(DateTime, default=datetime.utcnow) 
 
    ticket = relationship("Ticket", back_populates="comments") 
    commentator = relationship("User") 
