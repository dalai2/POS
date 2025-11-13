from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_tenant, get_current_user, require_admin
from app.models.tenant import Tenant
from app.models.user import User
from app.models.credit_payment import CreditPayment
from app.models.payment import Payment
from app.models.sale import Sale
from app.routes.status_history import create_status_history

router = APIRouter()


class CreditPaymentCreate(BaseModel):
    sale_id: int
    amount: float
    payment_method: str = "efectivo"  # "efectivo" or "tarjeta"
    notes: Optional[str] = None


class CreditPaymentResponse(BaseModel):
    id: int
    sale_id: int
    amount: float
    payment_method: str
    user_id: Optional[int]
    notes: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class CreditSaleDetail(BaseModel):
    id: int
    customer_name: Optional[str]
    customer_phone: Optional[str]
    total: float
    amount_paid: float
    balance: float
    credit_status: str
    vendedor_id: Optional[int]
    vendedor_email: Optional[str]
    created_at: str
    payments: List[CreditPaymentResponse]

    class Config:
        from_attributes = True


@router.get("/sales", response_model=List[CreditSaleDetail])
def get_credit_sales(
    status: Optional[str] = None,
    vendedor_id: Optional[int] = None,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Get all credit sales with optional filters"""
    from datetime import datetime, timedelta
    
    query = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito"
    )

    if status:
        query = query.filter(Sale.credit_status == status)

    if vendedor_id:
        query = query.filter(Sale.vendedor_id == vendedor_id)

    sales = query.order_by(Sale.created_at.desc()).all()
    
    # Verificar y actualizar estado vencido (75 días = 2 meses + 15 días)
    fecha_limite = datetime.utcnow() - timedelta(days=75)
    for sale in sales:
        balance = float(sale.total) - float(sale.amount_paid or 0)
        # Si tiene balance pendiente, no está pagado/cancelado, y han pasado 75 días
        if (balance > 0 and 
            sale.credit_status not in ['paid', 'cancelled', 'vencido'] and
            sale.created_at.replace(tzinfo=None) < fecha_limite):
            sale.credit_status = 'vencido'
            db.add(sale)
    
    # Commit cambios de estados
    db.commit()

    # Add payments and balance to each sale
    result = []
    for sale in sales:
        # Obtener pagos iniciales de la tabla Payment (anticipo)
        initial_payments_query = db.query(Payment).filter(
            Payment.sale_id == sale.id
        ).all()
        
        # Obtener abonos posteriores de CreditPayment
        credit_payments_query = db.query(CreditPayment).filter(
            CreditPayment.sale_id == sale.id
        ).all()
        
        # Combinar ambos tipos de pagos
        payments = []
        
        # Consolidar pagos iniciales (anticipo) en una sola entrada
        if initial_payments_query:
            # Sumar todos los pagos iniciales
            total_inicial = sum(float(p.amount) for p in initial_payments_query)
            metodo_efectivo = sum(float(p.amount) for p in initial_payments_query if p.method == 'cash')
            metodo_tarjeta = sum(float(p.amount) for p in initial_payments_query if p.method == 'card')
            
            # Determinar el método de pago a mostrar
            if metodo_efectivo > 0 and metodo_tarjeta > 0:
                metodo_display = f"mixto (E:${metodo_efectivo:.2f} T:${metodo_tarjeta:.2f})"
            elif metodo_tarjeta > 0:
                metodo_display = "card"
            else:
                metodo_display = "cash"
            
            # Agregar un solo registro consolidado para el anticipo inicial
            payments.append({
                "id": -initial_payments_query[0].id,  # ID negativo del primer pago
                "sale_id": sale.id,
                "amount": total_inicial,
                "payment_method": metodo_display,
                "user_id": sale.vendedor_id,
                "notes": "Anticipo inicial",
                "created_at": sale.created_at.isoformat()
            })
        
        # Agregar abonos posteriores
        for p in credit_payments_query:
            payments.append({
                "id": p.id,
                "sale_id": p.sale_id,
                "amount": float(p.amount),
                "payment_method": p.payment_method,
                "user_id": p.user_id,
                "notes": p.notes,
                "created_at": p.created_at.isoformat()
            })
        
        # Ordenar todos los pagos por fecha
        payments.sort(key=lambda x: x["created_at"])
        
        balance = float(sale.total) - float(sale.amount_paid or 0)
        
        # Obtener email del vendedor si existe
        vendedor_email = None
        if sale.vendedor_id:
            vendedor = db.query(User).filter(User.id == sale.vendedor_id).first()
            if vendedor:
                vendedor_email = vendedor.email
        
        result.append({
            "id": sale.id,
            "customer_name": sale.customer_name,
            "customer_phone": sale.customer_phone,
            "total": float(sale.total),
            "amount_paid": float(sale.amount_paid or 0),
            "balance": balance,
            "credit_status": sale.credit_status,
            "vendedor_id": sale.vendedor_id,
            "vendedor_email": vendedor_email,
            "created_at": sale.created_at.isoformat(),
            "payments": payments
        })
    
    return result


@router.post("/payments", response_model=CreditPaymentResponse)
def register_payment(
    data: CreditPaymentCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Register a payment (abono) for a credit sale"""
    # Verify sale exists and is a credit sale
    sale = db.query(Sale).filter(
        Sale.id == data.sale_id,
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito"
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Credit sale not found")
    
    # Verificar si está vencido (permitir pagos en ventas vencidas)
    # El estado cambiará a "paid" automáticamente cuando se pague completo
    
    # Calculate remaining balance
    balance = float(sale.total) - float(sale.amount_paid or 0)
    previous_paid = float(sale.amount_paid or 0)
    
    # Validate payment amount
    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")
    
    if data.amount > balance:
        raise HTTPException(status_code=400, detail="Payment amount exceeds remaining balance")
    
    # Create payment record
    payment = CreditPayment(
        tenant_id=tenant.id,
        sale_id=data.sale_id,
        amount=data.amount,
        payment_method=data.payment_method,
        user_id=current_user.id,
        notes=data.notes
    )
    db.add(payment)
    
    # Update sale
    sale.amount_paid = float(sale.amount_paid or 0) + data.amount
    old_status = sale.credit_status
    new_paid = sale.amount_paid
    new_balance = float(sale.total) - new_paid
    
    # Update status if fully paid
    if sale.amount_paid >= sale.total:
        sale.credit_status = "pagado"
    
    db.commit()
    db.refresh(payment)
    
    # Registrar cambio de estado si cambió
    if old_status != sale.credit_status:
        create_status_history(
            db=db,
            tenant_id=tenant.id,
            entity_type="sale",
            entity_id=sale.id,
            old_status=old_status,
            new_status=sale.credit_status,
            user_id=current_user.id,
            user_email=current_user.email,
            notes=f"Abono de ${data.amount:.2f} - Venta completamente pagada"
        )
    
    # NOTE: Ticket generation for abonos moved to frontend to match sales logic
    
    # Return payment as dict with serialized created_at
    return {
        "id": payment.id,
        "sale_id": payment.sale_id,
        "amount": float(payment.amount),
        "payment_method": payment.payment_method,
        "user_id": payment.user_id,
        "notes": payment.notes,
        "created_at": payment.created_at.isoformat()
    }
@router.get("/payments/{sale_id}", response_model=List[CreditPaymentResponse])
def get_sale_payments(
    sale_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Get all payments for a specific credit sale"""
    # Verify sale exists
    sale = db.query(Sale).filter(
        Sale.id == sale_id,
        Sale.tenant_id == tenant.id
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    payments_query = db.query(CreditPayment).filter(
        CreditPayment.sale_id == sale_id,
        CreditPayment.tenant_id == tenant.id
    ).order_by(CreditPayment.created_at.desc()).all()
    
    # Convert payments to dict format
    payments = [
        {
            "id": p.id,
            "sale_id": p.sale_id,
            "amount": float(p.amount),
            "payment_method": p.payment_method,
            "user_id": p.user_id,
            "notes": p.notes,
            "created_at": p.created_at.isoformat()
        }
        for p in payments_query
    ]
    
    return payments
@router.patch("/sales/{sale_id}/entregado")
def mark_as_delivered(
    sale_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Mark a credit sale as delivered"""
    sale = db.query(Sale).filter(
        Sale.id == sale_id,
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito"
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    old_status = sale.credit_status
    sale.credit_status = "entregado"
    db.commit()
    
    # Registrar en historial
    create_status_history(
        db=db,
        tenant_id=tenant.id,
        entity_type="sale",
        entity_id=sale.id,
        old_status=old_status,
        new_status="entregado",
        user_id=current_user.id,
        user_email=current_user.email,
        notes="Venta marcada como entregada"
    )
    
    return {"message": "Sale marked as delivered", "status": "entregado"}


@router.patch("/sales/{sale_id}/cancelado")
def mark_as_cancelled(
    sale_id: int,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Mark a credit sale as cancelled"""
    sale = db.query(Sale).filter(
        Sale.id == sale_id,
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito"
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    if sale.credit_status not in ['pendiente', 'vencido']:
        raise HTTPException(status_code=400, detail="Solo se pueden cancelar ventas pendientes o vencidas")
    
    old_status = sale.credit_status
    sale.credit_status = "cancelado"
    db.commit()
    
    # Registrar en historial
    create_status_history(
        db=db,
        tenant_id=tenant.id,
        entity_type="sale",
        entity_id=sale.id,
        old_status=old_status,
        new_status="cancelado",
        user_id=current_user.id,
        user_email=current_user.email,
        notes="Venta cancelada manualmente"
    )
    
    return {"message": "Sale marked as cancelled", "status": "cancelado"}


class StatusChangeRequest(BaseModel):
    status: str


@router.patch("/sales/{sale_id}/status")
def change_sale_status(
    sale_id: int,
    data: StatusChangeRequest,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Change credit sale status manually (admin/owner only)"""
    sale = db.query(Sale).filter(
        Sale.id == sale_id,
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito"
    ).first()
    
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Validar estados permitidos
    allowed_statuses = ['pendiente', 'pagado', 'entregado', 'vencido', 'cancelado']
    if data.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Debe ser uno de: {', '.join(allowed_statuses)}")
    
    # Validar que un apartado pagado no pueda moverse a pendiente o vencido
    if sale.credit_status == 'pagado' and data.status in ['pendiente', 'vencido']:
        raise HTTPException(
            status_code=400, 
            detail="Un apartado pagado no puede cambiar a estado pendiente o vencido"
        )
    
    old_status = sale.credit_status
    sale.credit_status = data.status
    db.commit()
    
    # Registrar en historial
    create_status_history(
        db=db,
        tenant_id=tenant.id,
        entity_type="sale",
        entity_id=sale.id,
        old_status=old_status,
        new_status=data.status,
        user_id=current_user.id,
        user_email=current_user.email,
        notes=f"Estado cambiado manualmente de {old_status} a {data.status}"
    )
    
    return {"message": "Status updated successfully", "status": data.status}

