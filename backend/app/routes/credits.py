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
from app.models.sale import Sale

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
    user_id: int
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
    current_user: User = Depends(require_admin)
):
    """Get all credit sales with optional filters"""
    query = db.query(Sale).filter(
        Sale.tenant_id == tenant.id,
        Sale.tipo_venta == "credito"
    )

    if status:
        query = query.filter(Sale.credit_status == status)

    if vendedor_id:
        query = query.filter(Sale.vendedor_id == vendedor_id)

    sales = query.order_by(Sale.created_at.desc()).all()

    # Add payments and balance to each sale
    result = []
    for sale in sales:
        payments_query = db.query(CreditPayment).filter(
            CreditPayment.sale_id == sale.id
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
        
        balance = float(sale.total) - float(sale.amount_paid or 0)
        
        result.append({
            "id": sale.id,
            "customer_name": sale.customer_name,
            "customer_phone": sale.customer_phone,
            "total": float(sale.total),
            "amount_paid": float(sale.amount_paid or 0),
            "balance": balance,
            "credit_status": sale.credit_status,
            "vendedor_id": sale.vendedor_id,
            "created_at": sale.created_at.isoformat(),
            "payments": payments
        })
    
    return result


@router.post("/payments", response_model=CreditPaymentResponse)
def register_payment(
    data: CreditPaymentCreate,
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(require_admin)
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
    
    # Calculate remaining balance
    balance = float(sale.total) - float(sale.amount_paid or 0)
    
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
    
    # Update status if fully paid
    if sale.amount_paid >= sale.total:
        sale.credit_status = "pagado"
    
    db.commit()
    db.refresh(payment)
    
    # Return payment as dict
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
    current_user: User = Depends(require_admin)
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

