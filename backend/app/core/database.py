from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.tenant import Base


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ejecutar migraciones automáticamente al importar el módulo
# Esto asegura que las columnas existan antes de que se use el modelo
try:
    from sqlalchemy import inspect as sqlalchemy_inspect
    inspector = sqlalchemy_inspect(engine)

    # Migración para notas_cliente en apartados
    if 'apartados' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('apartados')]
        if 'notas_cliente' not in columns:
            with engine.connect() as connection:
                connection.execute(text("ALTER TABLE apartados ADD COLUMN IF NOT EXISTS notas_cliente TEXT"))
                connection.commit()

    # Migración para vip_discount_pct en apartados
    if 'apartados' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('apartados')]
        if 'vip_discount_pct' not in columns:
            with engine.connect() as connection:
                connection.execute(text("ALTER TABLE apartados ADD COLUMN vip_discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0"))
                connection.commit()

    # Migración para agregar vip_discount_pct en pedidos
    if 'pedidos' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('pedidos')]
        if 'vip_discount_pct' not in columns:
            try:
                with engine.connect() as connection:
                    connection.execute(text("ALTER TABLE pedidos ADD COLUMN vip_discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0"))
                    connection.commit()
                    print("✅ Migración completada: columna vip_discount_pct agregada a pedidos")
            except Exception as e:
                print(f"⚠️ No se pudo agregar columna vip_discount_pct a pedidos: {e}")

    # Migración para quitar descuento_vip_pct en pedidos (si existe)
    if 'pedidos' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('pedidos')]
        if 'descuento_vip_pct' in columns:
            try:
                with engine.connect() as connection:
                    connection.execute(text("ALTER TABLE pedidos DROP COLUMN IF EXISTS descuento_vip_pct"))
                    connection.commit()
                    print("✅ Migración completada: columna descuento_vip_pct eliminada de pedidos")
            except Exception as e:
                print(f"⚠️ No se pudo eliminar columna descuento_vip_pct: {e}")


except Exception:
    # Si hay algún error (tabla no existe, etc), se ignorará
    # La migración se ejecutará en init_db() cuando se cree la tabla
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_migration_notas_cliente() -> None:
    """Ejecuta migración para agregar columna notas_cliente a apartados si no existe"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('apartados')]

        if 'notas_cliente' not in columns:
            print("Ejecutando migración: Agregar columna notas_cliente a apartados...")
            with engine.connect() as connection:
                connection.execute(text("ALTER TABLE apartados ADD COLUMN IF NOT EXISTS notas_cliente TEXT"))
                connection.commit()
            print("✅ Migración completada: columna notas_cliente agregada a apartados")
    except Exception as e:
        # Si la tabla no existe aún, se creará con create_all
        # Si hay otro error, lo ignoramos silenciosamente
        pass


def _run_migration_vip_discount() -> None:
    """Ejecuta migración para agregar columna vip_discount_pct a apartados si no existe"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('apartados')]

        if 'vip_discount_pct' not in columns:
            print("Ejecutando migración: Agregar columna vip_discount_pct a apartados...")
            with engine.connect() as connection:
                connection.execute(text("ALTER TABLE apartados ADD COLUMN vip_discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0"))
                connection.commit()
            print("✅ Migración completada: columna vip_discount_pct agregada a apartados")
    except Exception as e:
        # Si la tabla no existe aún, se creará con create_all
        # Si hay otro error, lo ignoramos silenciosamente
        pass


def _run_migration_vip_discount_pedidos() -> None:
    """Ejecuta migración para agregar columna vip_discount_pct a pedidos si no existe"""
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('pedidos')]

        if 'vip_discount_pct' not in columns:
            print("Ejecutando migración: Agregar columna vip_discount_pct a pedidos...")
            with engine.connect() as connection:
                connection.execute(text("ALTER TABLE pedidos ADD COLUMN vip_discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0"))
                connection.commit()
            print("✅ Migración completada: columna vip_discount_pct agregada a pedidos")
    except Exception as e:
        # Si la tabla no existe aún, se creará con create_all
        # Si hay otro error, lo ignoramos silenciosamente
        pass




def init_db() -> None:
    # Create tables in dev/test without running Alembic
    if settings.env in {"dev", "test"}:
        Base.metadata.create_all(bind=engine)

    # Ejecutar migraciones si es necesario
    _run_migration_notas_cliente()
    _run_migration_vip_discount()
    _run_migration_vip_discount_pedidos()


