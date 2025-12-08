from sqlalchemy import Column, Integer, String, ForeignKey 
from sqlalchemy.orm import relationship 
from app.database import Base 
 
class Role(Base): 
    __tablename__ = "roles" 
    id = Column(Integer, primary_key=True, index=True) 
    name = Column(String, unique=True, index=True) 
    users = relationship("User", back_populates="role") 
 
class Department(Base): 
    __tablename__ = "departments" 
    id = Column(Integer, primary_key=True, index=True) 
    name = Column(String, unique=True, index=True) 
    users = relationship("User", back_populates="department") 
    tickets = relationship("Ticket", back_populates="assigned_department") 
 
class User(Base): 
    __tablename__ = "users" 
    id = Column(Integer, primary_key=True, index=True) 
    email = Column(String, unique=True, index=True) 
    password_hash = Column(String) 
 
    role_id = Column(Integer, ForeignKey("roles.id")) 
    role = relationship("Role", back_populates="users") 
 
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True) 
    department = relationship("Department", back_populates="users") 
 
    created_tickets = relationship("Ticket", foreign_keys="[Ticket.created_by_user_id]", back_populates="creator") 
    assigned_tickets = relationship("Ticket", foreign_keys="[Ticket.assigned_support_id]", back_populates="assignee") 
    assigned_tickets = relationship("Ticket", foreign_keys="[Ticket.assigned_support_id]", back_populates="assignee") 
