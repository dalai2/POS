from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
from io import BytesIO

from app.core.database import get_db
from app.core.deps import get_tenant, get_current_user
from app.models.tenant import Tenant
from app.models.user import User
from app.models.product import Product
from app.models.metal_rate import MetalRate

router = APIRouter()


@router.post("/products/import")
async def import_products(
    file: UploadFile = File(...),
    mode: str = Form("add"),  # "add" or "replace"
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """
    Import products from Excel file
    Mode: 'add' = agregar nuevos, 'replace' = reemplazar existentes
    
    Excel columns:
    - codigo (required)
    - nombre (required) - also accepts 'name' for compatibility
    - marca
    - modelo
    - color
    - quilataje (cualquier tipo de metal, ej: 14k, Plata Gold, Oro Italiano)
    - tipo_joya
    - talla
    - peso_gramos
    - descuento_porcentaje
    - precio_manual (opcional, si se deja vacío se calcula automáticamente)
    - costo
    - stock
    """
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="El archivo debe ser Excel (.xlsx o .xls)")
    
    try:
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(BytesIO(contents))
        
        # Normalize column names (accept both 'name' and 'nombre')
        if 'nombre' in df.columns and 'name' not in df.columns:
            df['name'] = df['nombre']
        
        # Validate required columns (only codigo is required)
        required_cols = ['codigo']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Columnas requeridas faltantes: {', '.join(missing_cols)}"
            )
        
        # Get metal rates for price calculation
        metal_rates = {
            rate.metal_type: rate.rate_per_gram 
            for rate in db.query(MetalRate).filter(MetalRate.tenant_id == tenant.id).all()
        }
        
        added = 0
        updated = 0
        errors = []
        
        print(f"DEBUG: Import mode = {mode}")
        
        for idx, row in df.iterrows():
            try:
                codigo_raw = row.get('codigo')
                # Handle NaN values from pandas
                if pd.isna(codigo_raw):
                    errors.append(f"Fila {idx+2}: código es requerido")
                    continue
                
                codigo = str(codigo_raw).strip()
                name_raw = row.get('name')
                
                # Name is optional - if empty, leave it blank
                if pd.isna(name_raw):
                    name = ""
                else:
                    name = str(name_raw).strip()
                
                if not codigo:
                    errors.append(f"Fila {idx+2}: código es requerido")
                    continue
                
                # Check if product exists
                existing = db.query(Product).filter(
                    Product.tenant_id == tenant.id,
                    Product.codigo == codigo
                ).first()
                
                print(f"DEBUG: Fila {idx+2} - codigo={codigo}, existing={existing is not None}, mode={mode}")
                
                # Calculate price
                quilataje = str(row.get('quilataje', '')).strip() if pd.notna(row.get('quilataje')) else None
                peso_gramos = float(row.get('peso_gramos', 0)) if pd.notna(row.get('peso_gramos')) else None
                descuento_pct = float(row.get('descuento_porcentaje', 0)) if pd.notna(row.get('descuento_porcentaje')) else 0
                precio_manual = float(row.get('precio_manual')) if pd.notna(row.get('precio_manual')) else None
                
                # Auto-calculate price if no manual price
                if precio_manual:
                    precio_venta = precio_manual
                elif quilataje and peso_gramos and quilataje in metal_rates:
                    # Convert Decimal to float to avoid type mismatch
                    base_price = float(metal_rates[quilataje]) * peso_gramos
                    precio_venta = base_price - (base_price * descuento_pct / 100)
                else:
                    # Use costo with markup if available
                    costo = float(row.get('costo', 0)) if pd.notna(row.get('costo')) else 0
                    precio_venta = costo * 1.5 if costo > 0 else 0
                
                product_data = {
                    'name': name,
                    'codigo': codigo,
                    'marca': str(row.get('marca', '')).strip() if pd.notna(row.get('marca')) else None,
                    'modelo': str(row.get('modelo', '')).strip() if pd.notna(row.get('modelo')) else None,
                    'color': str(row.get('color', '')).strip() if pd.notna(row.get('color')) else None,
                    'quilataje': quilataje,
                    'base': str(row.get('base', '')).strip() if pd.notna(row.get('base')) else None,
                    'tipo_joya': str(row.get('tipo_joya', '')).strip() if pd.notna(row.get('tipo_joya')) else None,
                    'talla': str(row.get('talla', '')).strip() if pd.notna(row.get('talla')) else None,
                    'peso_gramos': peso_gramos,
                    'descuento_porcentaje': descuento_pct,
                    'precio_manual': precio_manual,
                    'costo': float(row.get('costo', 0)) if pd.notna(row.get('costo')) else 0,
                    'cost_price': float(row.get('costo', 0)) if pd.notna(row.get('costo')) else 0,
                    'precio_venta': precio_venta,
                    'price': precio_venta,
                    'stock': int(row.get('stock', 0)) if pd.notna(row.get('stock')) else 0,
                    'codigo': str(row.get('codigo', '')).strip() if pd.notna(row.get('codigo')) else None,
                    'active': True,
                    'tenant_id': tenant.id
                }
                
                if existing and mode == 'replace':
                    # Update existing product
                    print(f"DEBUG: Updating existing product {codigo}")
                    for key, value in product_data.items():
                        if key != 'tenant_id':  # Don't update tenant_id
                            setattr(existing, key, value)
                    updated += 1
                elif not existing:
                    # Add new product
                    print(f"DEBUG: Adding new product {codigo}")
                    new_product = Product(**product_data)
                    db.add(new_product)
                    added += 1
                else:
                    print(f"DEBUG: Skipping product {codigo} (exists and mode is add)")
                # If mode is 'add' and product exists, skip it
                
            except Exception as e:
                errors.append(f"Fila {idx+2}: {str(e)}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "added": added,
            "updated": updated,
            "errors": errors,
            "total_rows": len(df)
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando archivo: {str(e)}")


@router.get("/products/export-template")
async def export_template():
    """Download Excel template for product import"""
    
    # Create sample data
    data = {
        'codigo': ['AN-001', 'COL-002'],
        'nombre': ['Anillo Oro 14K', 'Collar Plata Gold'],
        'marca': ['DEMO', 'DEMO'],
        'modelo': ['M-001', 'M-002'],
        'color': ['Amarillo', 'Plata'],
        'quilataje': ['14k', 'Plata Gold'],
        'tipo_joya': ['Anillo', 'Collar'],
        'talla': ['7', ''],
        'peso_gramos': [3.5, 8.0],
        'descuento_porcentaje': [10, 5],
        'precio_manual': ['', ''],  # Dejar vacío para cálculo automático
        'costo': [100, 80],
        'stock': [5, 10]
    }
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Productos')
        
        # Get worksheet
        worksheet = writer.sheets['Productos']
        
        # Add instructions in a second sheet
        instructions = pd.DataFrame({
            'Campo': [
                'codigo', 'nombre', 'quilataje', 'peso_gramos', 
                'descuento_porcentaje', 'precio_manual', 'costo', 'stock'
            ],
            'Descripción': [
                'Código único del producto (REQUERIDO)',
                'Nombre del producto (REQUERIDO)',
                'Quilataje: cualquier tipo de metal (ej: 14k, Plata Gold, Oro Italiano)',
                'Peso en gramos (para cálculo automático de precio)',
                'Descuento porcentaje (0-100)',
                'Dejar vacío para cálculo automático, o poner precio fijo',
                'Costo del producto',
                'Cantidad en inventario'
            ]
        })
        instructions.to_excel(writer, index=False, sheet_name='Instrucciones')
    
    output.seek(0)
    
    from fastapi.responses import StreamingResponse
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_productos.xlsx"}
    )


@router.get("/products/export")
async def export_products(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_tenant),
    current_user: User = Depends(get_current_user)
):
    """Export all products to Excel file"""

    try:
        # Get all active products for the tenant
        products = db.query(Product).filter(
            Product.tenant_id == tenant.id,
            Product.active == True
        ).all()

        if not products:
            raise HTTPException(status_code=404, detail="No hay productos para exportar")

        # Prepare data for export
        data = []
        for product in products:
            row = {
                'codigo': product.codigo or '',
                'nombre': product.name,
                'marca': product.marca or '',
                'modelo': product.modelo or '',
                'color': product.color or '',
                'quilataje': product.quilataje or '',
                'tipo_joya': product.tipo_joya or '',
                'talla': product.talla or '',
                'peso_gramos': product.peso_gramos or '',
                'descuento_porcentaje': product.descuento_porcentaje or '',
                'precio_manual': product.precio_manual or '',
                'costo': product.costo or product.cost_price or '',
                'stock': product.stock or ''
            }
            data.append(row)

        df = pd.DataFrame(data)

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Productos')

            # Get worksheet
            worksheet = writer.sheets['Productos']

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Max width of 50
                worksheet.column_dimensions[column_letter].width = adjusted_width

        output.seek(0)

        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=productos_exportados.xlsx"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exportando productos: {str(e)}")
