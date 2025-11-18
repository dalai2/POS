from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.tenant import Base


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ejecutar migración de notas_cliente automáticamente al importar el módulo
# Esto asegura que la columna exista antes de que se use el modelo
try:
    from sqlalchemy import inspect as sqlalchemy_inspect
    inspector = sqlalchemy_inspect(engine)
    # Verificar si la tabla existe antes de intentar inspeccionarla
    if 'apartados' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('apartados')]
        if 'notas_cliente' not in columns:
            with engine.connect() as connection:
                connection.execute(text("ALTER TABLE apartados ADD COLUMN IF NOT EXISTS notas_cliente TEXT"))
                connection.commit()
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


def init_db() -> None:
    # Create tables in dev/test without running Alembic
    if settings.env in {"dev", "test"}:
        Base.metadata.create_all(bind=engine)
    
    # Ejecutar migración de notas_cliente si es necesario
    _run_migration_notas_cliente()


