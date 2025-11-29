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
    - modelo
    - color
    - quilataje (cualquier tipo de metal, ej: 14k, Plata Gold, Oro Italiano)
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
        
        # First, normalize column names to lowercase and strip spaces
        df.columns = df.columns.str.lower().str.strip()
        
        # Then map column name variations to standard names (all keys are lowercase since we normalized above)
        column_mapping = {
            # Weight variations
            'peso': 'peso_gramos',
            'peso en gramos': 'peso_gramos',
            'peso_gramos': 'peso_gramos',
            # Discount variations
            'descuento': 'descuento_porcentaje',
            'descuento_porcentaje': 'descuento_porcentaje',
            'descuento %': 'descuento_porcentaje',
            # Price variations
            'precio manual': 'precio_manual',
            'precio_manual': 'precio_manual',
            'precio': 'precio_manual',  # Only if precio_manual doesn't exist
            # Stock variations
            'piezas': 'stock',
            'stock': 'stock',
            'cantidad': 'stock',
            # Name variations
            'name': 'nombre',
            'nombre': 'nombre',
        }
        
        # Apply mapping, but don't overwrite if target already exists
        rename_dict = {}
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                rename_dict[old_name] = new_name
        
        if rename_dict:
            df = df.rename(columns=rename_dict)
        
        # Normalize column names (accept both 'name' and 'nombre')
        if 'nombre' in df.columns and 'name' not in df.columns:
            df['name'] = df['nombre']
        
        # Debug: verificar columnas después de normalizar
        import sys
        print(f"DEBUG IMPORT PRODUCTS: Columnas después de normalizar: {list(df.columns)}", file=sys.stderr)
        print(f"DEBUG IMPORT PRODUCTS: Columnas después de normalizar: {list(df.columns)}")
        if 'quilataje' in df.columns:
            print(f"DEBUG IMPORT PRODUCTS: Columna 'quilataje' encontrada", file=sys.stderr)
            sample_values = df['quilataje'].head(3).tolist()
            print(f"DEBUG IMPORT PRODUCTS: Primeros 3 valores de quilataje: {sample_values}", file=sys.stderr)
        else:
            print("DEBUG IMPORT PRODUCTS: ERROR - Columna 'quilataje' NO encontrada", file=sys.stderr)
        
        # Validate required columns (only codigo is required)
        required_cols = ['codigo']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Columnas requeridas faltantes: {', '.join(missing_cols)}"
            )
        
        # Get metal rates for price calculation (case-insensitive lookup)
        metal_rates = {}
        metal_rates_lower = {}  # For case-insensitive lookup
        for rate in db.query(MetalRate).filter(MetalRate.tenant_id == tenant.id).all():
            metal_rates[rate.metal_type] = rate.rate_per_gram
            metal_rates_lower[rate.metal_type.lower()] = rate.rate_per_gram
        
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
                # Check both 'name' and 'nombre' columns
                name_raw = None
                if 'name' in df.columns:
                    name_raw = row['name']
                elif 'nombre' in df.columns:
                    name_raw = row['nombre']
                
                # Name is optional - if empty, leave it blank
                if pd.isna(name_raw) or name_raw == '':
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
                
                # Process quilataje with improved validation (quilataje is optional)
                quilataje = None
                if 'quilataje' in df.columns:
                    try:
                        raw_quilataje = row['quilataje']  # Direct access to pandas Series
                        if pd.notna(raw_quilataje):
                            quilataje_str = str(raw_quilataje).strip()
                            if quilataje_str and quilataje_str.lower() != 'nan' and quilataje_str.lower() != 'none':
                                quilataje = quilataje_str
                    except (KeyError, IndexError):
                        # Silently skip - quilataje is optional
                        pass
                
                # Calculate price - use direct access for pandas Series
                peso_gramos = None
                if 'peso_gramos' in df.columns:
                    try:
                        peso_val = row['peso_gramos']
                        if pd.notna(peso_val) and str(peso_val).strip() != '':
                            peso_gramos = float(peso_val)
                    except (ValueError, TypeError, KeyError):
                        pass
                
                descuento_pct = 0
                if 'descuento_porcentaje' in df.columns:
                    try:
                        desc_val = row['descuento_porcentaje']
                        if pd.notna(desc_val) and str(desc_val).strip() != '':
                            descuento_pct = float(desc_val)
                    except (ValueError, TypeError, KeyError):
                        pass
                
                precio_manual = None
                if 'precio_manual' in df.columns:
                    try:
                        precio_val = row['precio_manual']
                        if pd.notna(precio_val) and str(precio_val).strip() != '':
                            precio_manual = float(precio_val)
                    except (ValueError, TypeError, KeyError):
                        pass
                
                # Calculate costo (needed for price calculation)
                costo_value = 0
                if 'costo' in df.columns:
                    try:
                        costo_val = row['costo']
                        if pd.notna(costo_val) and str(costo_val).strip() != '':
                            costo_value = float(costo_val)
                    except (ValueError, TypeError, KeyError):
                        pass
                
                # Auto-calculate price if no manual price
                if precio_manual:
                    precio_venta = precio_manual
                elif quilataje and peso_gramos:
                    # Case-insensitive lookup for quilataje
                    quilataje_lower = quilataje.lower()
                    if quilataje in metal_rates:
                        rate_per_gram = metal_rates[quilataje]
                    elif quilataje_lower in metal_rates_lower:
                        rate_per_gram = metal_rates_lower[quilataje_lower]
                    else:
                        rate_per_gram = None
                    
                    if rate_per_gram:
                        # Convert Decimal to float to avoid type mismatch
                        base_price = float(rate_per_gram) * peso_gramos
                        precio_venta = base_price - (base_price * descuento_pct / 100)
                    else:
                        # Use costo with markup if available
                        if costo_value > 0:
                            precio_venta = costo_value * 1.5
                        else:
                            precio_venta = 0
                else:
                    # Use costo with markup if available
                    if costo_value > 0:
                        precio_venta = costo_value * 1.5
                    else:
                        precio_venta = 0

                # Process other fields with direct access
                marca_value = None
                if 'marca' in df.columns:
                    try:
                        marca_val = row['marca']
                        if pd.notna(marca_val) and str(marca_val).strip() != '':
                            marca_value = str(marca_val).strip()
                    except (KeyError, IndexError):
                        pass

                modelo_value = None
                if 'modelo' in df.columns:
                    try:
                        modelo_val = row['modelo']
                        if pd.notna(modelo_val) and str(modelo_val).strip() != '':
                            modelo_value = str(modelo_val).strip()
                    except (KeyError, IndexError):
                        pass

                color_value = None
                if 'color' in df.columns:
                    try:
                        color_val = row['color']
                        if pd.notna(color_val) and str(color_val).strip() != '':
                            color_value = str(color_val).strip()
                    except (KeyError, IndexError):
                        pass

                base_value = None
                if 'base' in df.columns:
                    try:
                        base_val = row['base']
                        if pd.notna(base_val) and str(base_val).strip() != '':
                            base_value = str(base_val).strip()
                    except (KeyError, IndexError):
                        pass

                tipo_joya_value = None
                if 'tipo_joya' in df.columns:
                    try:
                        tipo_val = row['tipo_joya']
                        if pd.notna(tipo_val) and str(tipo_val).strip() != '':
                            tipo_joya_value = str(tipo_val).strip()
                    except (KeyError, IndexError):
                        pass

                talla_value = None
                if 'talla' in df.columns:
                    try:
                        talla_val = row['talla']
                        if pd.notna(talla_val) and str(talla_val).strip() != '':
                            talla_value = str(talla_val).strip()
                    except (KeyError, IndexError):
                        pass

                stock_value = 0
                if 'stock' in df.columns:
                    try:
                        stock_val = row['stock']
                        if pd.notna(stock_val) and str(stock_val).strip() != '':
                            stock_value = int(float(stock_val))  # Convert to float first in case it's a decimal
                    except (ValueError, TypeError, KeyError):
                        pass
                
                product_data = {
                    'name': name,
                    'codigo': codigo,
                    'marca': marca_value,
                    'modelo': modelo_value,
                    'color': color_value,
                    'quilataje': quilataje,
                    'base': base_value,
                    'tipo_joya': tipo_joya_value,
                    'talla': talla_value,
                    'peso_gramos': peso_gramos,
                    'descuento_porcentaje': descuento_pct,
                    'precio_manual': precio_manual,
                    'costo': costo_value,
                    'cost_price': costo_value,
                    'precio_venta': precio_venta,
                    'price': precio_venta,
                    'stock': stock_value,
                    'active': True,
                    'tenant_id': tenant.id
                }
                
                if existing:
                    # Update existing product (both 'add' and 'replace' modes update)
                    print(f"DEBUG: Updating existing product {codigo}")
                    for key, value in product_data.items():
                        if key != 'tenant_id':  # Don't update tenant_id
                            setattr(existing, key, value)
                    updated += 1
                else:
                    # Add new product
                    print(f"DEBUG: Adding new product {codigo}")
                    new_product = Product(**product_data)
                    db.add(new_product)
                    added += 1
                
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
        'modelo': ['M-001', 'M-002'],
        'color': ['Amarillo', 'Plata'],
        'quilataje': ['14k', 'Plata Gold'],
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
                'modelo': product.modelo or '',
                'color': product.color or '',
                'quilataje': product.quilataje or '',
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
