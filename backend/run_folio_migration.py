import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    print("Ejecutando migración de folios...")

    try:
        # Crear conexión a la base de datos
        engine = create_engine(settings.database_url)

        # Ejecutar la migración paso a paso
        with engine.connect() as connection:
            # 1. Agregar columna folio_apartado a tabla sales
            print("Agregando columna folio_apartado a sales...")
            connection.execute(text("ALTER TABLE sales ADD COLUMN IF NOT EXISTS folio_apartado VARCHAR(50)"))
            connection.commit()

            # 2. Crear índice para folio_apartado
            print("Creando índice para folio_apartado...")
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_sales_folio_apartado ON sales (folio_apartado)"))
            connection.commit()

            # 3. Generar folios para apartados existentes
            print("Generando folios para apartados existentes...")
            connection.execute(text("""
                UPDATE sales
                SET folio_apartado = 'APT-' || LPAD(id::text, 6, '0')
                WHERE tipo_venta = 'credito'
                AND folio_apartado IS NULL
            """))
            connection.commit()

            # 4. Agregar columna folio_pedido a tabla pedidos
            print("Agregando columna folio_pedido a pedidos...")
            connection.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS folio_pedido VARCHAR(50)"))
            connection.commit()

            # 5. Crear índice para folio_pedido
            print("Creando índice para folio_pedido...")
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_pedidos_folio_pedido ON pedidos (folio_pedido)"))
            connection.commit()

            # 6. Generar folios para pedidos existentes
            print("Generando folios para pedidos existentes...")
            connection.execute(text("""
                UPDATE pedidos
                SET folio_pedido = 'PED-' || LPAD(id::text, 6, '0')
                WHERE folio_pedido IS NULL
            """))
            connection.commit()

            print("✅ Migración completada exitosamente")

    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

    return True

if __name__ == "__main__":
    run_migration()
