from app.core.config import settings
from sqlalchemy import create_engine, text

def verify_migration():
    print("Verificando migración de folios...")

    try:
        engine = create_engine(settings.database_url)

        with engine.connect() as conn:
            # Verificar que la columna existe
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'pedidos'
                AND column_name = 'folio_pedido'
            """))

            if result.fetchone():
                print("✅ Columna folio_pedido encontrada en la tabla pedidos")
            else:
                print("❌ Columna folio_pedido NO encontrada")
                return

            # Verificar algunos folios generados
            result = conn.execute(text("""
                SELECT id, folio_pedido, cliente_nombre
                FROM pedidos
                ORDER BY id DESC
                LIMIT 3
            """))

            rows = result.fetchall()
            if rows:
                print("📄 Folios generados:")
                for row in rows:
                    print(f"  ID {row[0]}: {row[1]} - {row[2]}")
            else:
                print("📄 No hay pedidos en la base de datos")

    except Exception as e:
        print(f"❌ Error verificando migración: {e}")

if __name__ == "__main__":
    verify_migration()







