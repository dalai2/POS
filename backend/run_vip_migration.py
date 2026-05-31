import os
from sqlalchemy import create_engine, text

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

sql_file = "../migration_vip_discount.sql"

if __name__ == "__main__":
    try:
        with open(sql_file, "r") as f:
            sql_queries = f.read().split(";")
            
        with engine.connect() as connection:
            for query in sql_queries:
                q = query.strip()
                if q:
                    print(f"Executing: {q}")
                    connection.execute(text(q))
            connection.commit()
            print("✅ Migration successful: descuento_vip_pct added to apartados and ventas_contado.")
    except Exception as e:
        print(f"Error during migration: {e}")
