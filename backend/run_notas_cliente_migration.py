"""
Script para ejecutar migración: Agregar columna notas_cliente a tabla apartados
"""
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    print("Ejecutando migración: Agregar columna notas_cliente a apartados...")

    try:
        # Crear conexión a la base de datos
        engine = create_engine(settings.database_url)

        # Ejecutar la migración
        with engine.connect() as connection:
            print("Agregando columna notas_cliente a tabla apartados...")
            connection.execute(text("ALTER TABLE apartados ADD COLUMN IF NOT EXISTS notas_cliente TEXT"))
            connection.commit()
            
            # Verificar que la columna se agregó correctamente
            print("Verificando que la columna se agregó correctamente...")
            result = connection.execute(text("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = 'apartados' 
                AND column_name = 'notas_cliente'
            """))
            
            row = result.fetchone()
            if row:
                print(f"✅ Columna agregada correctamente:")
                print(f"   - Nombre: {row[0]}")
                print(f"   - Tipo: {row[1]}")
                print(f"   - Nullable: {row[2]}")
                print(f"   - Default: {row[3]}")
            else:
                print("⚠️  Advertencia: No se pudo verificar la columna")
            
            connection.commit()
            
        print("✅ Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando migración: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)

