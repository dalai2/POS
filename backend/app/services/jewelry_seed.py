"""
Seed script for jewelry store demo data
"""
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.user import User
from app.models.product import Product
from app.models.metal_rate import MetalRate
from app.models.sale import Sale, SaleItem
from app.models.credit_payment import CreditPayment


def seed_jewelry_demo(db: Session):
    """Seed demo data for jewelry store"""
    
    # Check if demo tenant exists
    tenant = db.query(Tenant).filter(Tenant.slug == 'demo').first()
    if not tenant:
        tenant = Tenant(name='Demo Joyería', slug='demo')
        db.add(tenant)
        db.flush()
        
        # Create owner user
        owner = User(
            email='owner@demo.com',
            hashed_password=hash_password('secret123'),
            role='owner',
            tenant_id=tenant.id
        )
        db.add(owner)
        db.flush()
    
    # Create additional users (vendedores)
    users_data = [
        ('vendedor1@demo.com', 'Vendedor 1', 'cashier'),
        ('vendedor2@demo.com', 'Vendedor 2', 'cashier'),
    ]
    
    for email, name, role in users_data:
        existing = db.query(User).filter(User.email == email, User.tenant_id == tenant.id).first()
        if not existing:
            user = User(
                email=email,
                hashed_password=hash_password('demo123'),
                role=role,
                tenant_id=tenant.id
            )
            db.add(user)
    
    db.flush()
    
    # Create metal rates
    metal_rates_data = [
        # Oro
        ('10k', 25.50),
        ('14k', 35.75),
        ('18k', 45.90),
        ('oro_italiano', 52.00),
        # Plata
        ('plata_gold', 15.50),
        ('plata_silver', 12.25),
    ]
    
    for metal_type, rate in metal_rates_data:
        existing = db.query(MetalRate).filter(
            MetalRate.tenant_id == tenant.id,
            MetalRate.metal_type == metal_type
        ).first()
        
        if not existing:
            metal_rate = MetalRate(
                tenant_id=tenant.id,
                metal_type=metal_type,
                rate_per_gram=rate
            )
            db.add(metal_rate)
    
    db.flush()
    
    # Create sample jewelry products - TODOS con quilataje y peso para precios dinámicos
    # (nombre, codigo, marca, modelo, tipo_joya, quilataje, peso_gramos, descuento_pct, talla)
    products_data = [
        # Anillos de Oro - precio calculado automáticamente
        ('Anillo Solitario 14K', 'AN-001', 'Elegance', 'SOL-14', 'Anillo', '14k', 3.5, 10, '7'),
        ('Anillo Compromiso 18K', 'AN-002', 'Royal', 'COM-18', 'Anillo', '18k', 4.2, 15, '6'),
        ('Anillo Oro Italiano', 'AN-003', 'Italiano', 'ITA-01', 'Anillo', 'oro_italiano', 5.0, 20, '8'),
        ('Anillo 10K Clásico', 'AN-004', 'Classic', 'CLA-10', 'Anillo', '10k', 2.8, 5, '7'),
        ('Anillo Diamante 18K', 'AN-005', 'Luxury', 'DIA-18', 'Anillo', '18k', 5.5, 12, '6.5'),
        
        # Collares de Oro
        ('Cadena Oro 14K 50cm', 'COL-001', 'Elegance', 'CAD-14-50', 'Collar', '14k', 8.5, 5, ''),
        ('Collar Corazón 10K', 'COL-002', 'Lovely', 'COR-10', 'Collar', '10k', 6.2, 8, ''),
        ('Gargantilla 18K', 'COL-003', 'Royal', 'GAR-18', 'Collar', '18k', 12.5, 10, ''),
        ('Cadena Italiana', 'COL-004', 'Italiano', 'CAD-ITA', 'Collar', 'oro_italiano', 15.0, 15, ''),
        
        # Pulseras de Oro
        ('Pulsera Eslabones 14K', 'PUL-001', 'Elegance', 'ESL-14', 'Pulsera', '14k', 7.3, 12, ''),
        ('Pulsera Oro Italiano', 'PUL-002', 'Italiano', 'PUL-ITA', 'Pulsera', 'oro_italiano', 9.5, 18, ''),
        ('Pulsera Tennis 18K', 'PUL-003', 'Luxury', 'TEN-18', 'Pulsera', '18k', 11.0, 8, ''),
        ('Brazalete 10K', 'PUL-004', 'Classic', 'BRA-10', 'Pulsera', '10k', 5.8, 7, ''),
        
        # Aretes de Oro
        ('Aretes Diamante 18K', 'ARE-001', 'Luxury', 'DIA-18', 'Aretes', '18k', 2.8, 10, ''),
        ('Aretes Argolla 14K', 'ARE-002', 'Elegance', 'ARG-14', 'Aretes', '14k', 3.2, 8, ''),
        ('Aretes Botón 10K', 'ARE-003', 'Classic', 'BOT-10', 'Aretes', '10k', 1.5, 5, ''),
        ('Aretes Colgantes Italiano', 'ARE-004', 'Italiano', 'COL-ITA', 'Aretes', 'oro_italiano', 4.2, 12, ''),
        
        # Joyería de Plata
        ('Anillo Plata Gold', 'AN-P001', 'Silver Line', 'PG-001', 'Anillo', 'plata_gold', 4.5, 5, '7'),
        ('Collar Plata Silver', 'COL-P001', 'Silver Line', 'PS-001', 'Collar', 'plata_silver', 12.0, 10, ''),
        ('Pulsera Plata Gold', 'PUL-P001', 'Silver Line', 'PG-002', 'Pulsera', 'plata_gold', 8.5, 8, ''),
        ('Aretes Plata Silver', 'ARE-P001', 'Silver Line', 'PS-002', 'Aretes', 'plata_silver', 3.8, 12, ''),
        ('Gargantilla Plata Gold', 'COL-P002', 'Silver Line', 'PG-003', 'Collar', 'plata_gold', 15.5, 6, ''),
        ('Tobillera Plata Silver', 'TOB-P001', 'Silver Line', 'PS-TOB', 'Tobillera', 'plata_silver', 7.2, 8, ''),
    ]
    
    for name, codigo, marca, modelo, tipo_joya, quilataje, peso_gramos, descuento_pct, talla in products_data:
        existing = db.query(Product).filter(
            Product.tenant_id == tenant.id,
            Product.codigo == codigo
        ).first()
        
        if not existing:
            # Get metal rate
            rate = db.query(MetalRate).filter(
                MetalRate.tenant_id == tenant.id,
                MetalRate.metal_type == quilataje
            ).first()
            
            # Calculate price based on metal rate
            if rate:
                base_price = float(rate.rate_per_gram) * peso_gramos
                precio_venta = base_price - (base_price * descuento_pct / 100)
                # Cost is approximately 70% of sale price for demo purposes
                costo_calculado = precio_venta * 0.70
            else:
                precio_venta = 100.00  # Fallback
                costo_calculado = 70.00
            
            # Determine color based on metal type
            if quilataje in ['10k', '14k', '18k', 'oro_italiano']:
                color = 'Amarillo'
            elif quilataje in ['plata_gold', 'plata_silver']:
                color = 'Plata'
            else:
                color = 'N/A'
            
            product = Product(
                name=name,
                codigo=codigo,
                marca=marca,
                modelo=modelo,
                color=color,
                tipo_joya=tipo_joya,
                quilataje=quilataje,
                base='Oro' if quilataje in ['10k', '14k', '18k', 'oro_italiano'] else 'Plata',
                talla=talla if talla else None,
                peso_gramos=peso_gramos,
                descuento_porcentaje=descuento_pct,
                costo=costo_calculado,
                cost_price=costo_calculado,
                precio_venta=precio_venta,
                price=precio_venta,
                stock=5,
                active=True,
                tenant_id=tenant.id,
                sku=f'SKU-{codigo}',
                barcode=f'BAR-{codigo}'
            )
            db.add(product)
    
    db.commit()
    print(f"Jewelry demo data seeded for tenant '{tenant.slug}'")

