from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import case 
from app.database import get_db
from app.models.ticket import Ticket, Comment
from app.models.user import User, Department, Role
from app.schemas.ticket import TicketCreate, TicketResponse, CommentCreate
from app.core.auth import get_current_user, get_department, get_support
from typing import List, Optional

router = APIRouter(tags=["Tickets"])

@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_new_ticket(
    ticket_data: TicketCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Aktif departmanlari cek
    department_names = [d.name for d in db.query(Department).all()]

    # YAPAY ZEKA KULLANARAK OTOMATIK KATEGORIZE ETME (ya da user'dan gelen department_name kullan)
    if ticket_data.department_name in department_names:
        assigned_department_name = ticket_data.department_name
    else:
        assigned_department_name = department_names[0] if department_names else None
    
    if not assigned_department_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hiçbir departman bulunamadı.")

    department = db.query(Department).filter(Department.name == assigned_department_name).first()
    if not department:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Departman bulunamadı.")

    new_ticket = Ticket(
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        created_by_user_id=current_user.id,
        assigned_department_id=department.id, 
        status="Open"
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket

@router.get("/department", response_model=List[TicketResponse])
def list_department_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_department),
    status_filter: Optional[str] = None,
    sort_by_priority: Optional[bool] = False
):
    """Departman yöneticisi - departmanına ait tüm ticket'ları görebilir."""
    query = db.query(Ticket).filter(
        Ticket.assigned_department_id == current_user.department_id
    )

    if status_filter:
        query = query.filter(Ticket.status == status_filter)

    if sort_by_priority:
        priority_order = case(
            (Ticket.priority == 'High', 1),
            (Ticket.priority == 'Medium', 2),
            (Ticket.priority == 'Low', 3),
            else_=4
        ).label("priority_order")
        query = query.order_by(priority_order)

    return query.all()

@router.get("/support", response_model=List[TicketResponse])
def list_support_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support)
):
    """Support personeli - kendine atanmış ticket'ları görebilir."""
    return db.query(Ticket).filter(
        Ticket.assigned_support_id == current_user.id
    ).all()

@router.get("/my", response_model=List[TicketResponse])
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tickets = db.query(Ticket).filter(Ticket.created_by_user_id == current_user.id).all()
    return tickets

@router.put("/{ticket_id}/assign")
def assign_support_to_ticket(
    ticket_id: int, 
    support_email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_department) 
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    support_user = db.query(User).filter(User.email == support_email, User.role.name == "support").first()
    
    if not ticket or not support_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket veya Destek Personeli bulunamadi.")
    
    ticket.assigned_support_id = support_user.id
    ticket.status = "In Progress"
    db.commit()

    return {"message": f"Ticket {ticket_id} basariyla {support_user.email} kullanicisina atandi."}

@router.put("/{ticket_id}/assign-department")
def assign_ticket_to_department(
    ticket_id: int, 
    department_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin - ticket'ı departmana atama."""
    if current_user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işleme yalnızca Admin yetkilidir.")
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket bulunamadi.")
    
    department = db.query(Department).filter(Department.name == department_name).first()
    if not department:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departman bulunamadi.")
    
    ticket.assigned_department_id = department.id
    ticket.status = "Open"
    db.commit()

    return {"message": f"Ticket {ticket_id} basariyla {department_name} departmanına atandi."}

@router.put("/{ticket_id}/status")
def update_ticket_status(
    ticket_id: int, 
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_support) 
):
    valid_statuses = ["Open", "In Progress", "Resolved", "Closed"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Gecersiz durum.")

    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket bulunamadi.")
    
    old_status = ticket.status
    ticket.status = new_status
    db.commit()

    return {"message": f"Ticket {ticket_id} durumu '{new_status}' olarak guncellendi."}

@router.post("/{ticket_id}/comment", status_code=status.HTTP_201_CREATED)
def add_comment_to_ticket(
    ticket_id: int, 
    comment_data: CommentCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket bulunamadi.")
        
    is_owner = ticket.created_by_user_id == current_user.id
    is_support = current_user.role.name in ["support", "department", "admin"]
    
    if not is_owner and not is_support:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu ticket'a yorum yapma yetkiniz yok.")

    new_comment = Comment(
        ticket_id=ticket_id,
        user_id=current_user.id,
        content=comment_data.content
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return {"message": "Yorum basariyla eklendi.", "comment_id": new_comment.id}
    
@router.get("/", response_model=List[TicketResponse])
def list_all_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), 
    department_filter: Optional[str] = None, 
    status_filter: Optional[str] = None,     
    sort_by_priority: Optional[bool] = False 
):
    if current_user.role.name not in ["admin", "department"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işleme yalnızca Admin yetkilidir.")
        
    query = db.query(Ticket)

    if department_filter:
        if department_filter != "":
            department = db.query(Department).filter(Department.name == department_filter).first()
        if department:
            query = query.filter(Ticket.assigned_department_id == department.id)

    if status_filter:
        if status_filter != "":
            query = query.filter(Ticket.status == status_filter)

    if sort_by_priority:
        priority_order = case(
            (Ticket.priority == 'High', 1),
            (Ticket.priority == 'Medium', 2),
            (Ticket.priority == 'Low', 3),
            else_=4
        ).label("priority_order")
        query = query.order_by(priority_order)
        
    return query.all()