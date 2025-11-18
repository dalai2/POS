import os
from typing import Dict
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection

from app.core.config import settings


def get_tenant_slugs(conn: Connection) -> Dict[int, str]:
	result = conn.execute(text("SELECT id, COALESCE(slug, id::text) AS slug FROM tenants"))
	return {row[0]: row[1] for row in result.fetchall()}


def ensure_counters(conn: Connection) -> None:
	# Create missing counters for each tenant and tipo
	conn.execute(text("""
		INSERT INTO folio_counters (tenant_id, tipo, next_seq)
		SELECT t.id, x.tipo, 1
		FROM tenants t
		CROSS JOIN (VALUES ('VENTA'), ('APARTADO')) AS x(tipo)
		LEFT JOIN folio_counters fc ON fc.tenant_id = t.id AND fc.tipo = x.tipo
		WHERE fc.id IS NULL
	"""))

	# Try to align next_seq with existing max sequences if any (parsing last 6 digits)
	# VENTA from sales.folio_venta
	conn.execute(text("""
		WITH max_seq AS (
			SELECT tenant_id, COALESCE(MAX(CAST(SPLIT_PART(folio_venta, '-', 3) AS INTEGER)), 0) AS mx
			FROM sales
			WHERE folio_venta IS NOT NULL AND folio_venta <> ''
			GROUP BY tenant_id
		)
		UPDATE folio_counters fc
		SET next_seq = GREATEST(fc.next_seq, ms.mx + 1)
		FROM max_seq ms
		WHERE fc.tenant_id = ms.tenant_id AND fc.tipo = 'VENTA'
	"""))

	# APARTADO from apartados.folio_apartado (if pre-existing)
	conn.execute(text("""
		WITH max_seq AS (
			SELECT tenant_id, COALESCE(MAX(CAST(SPLIT_PART(folio_apartado, '-', 3) AS INTEGER)), 0) AS mx
			FROM apartados
			WHERE folio_apartado IS NOT NULL AND folio_apartado <> ''
			GROUP BY tenant_id
		)
		UPDATE folio_counters fc
		SET next_seq = GREATEST(fc.next_seq, ms.mx + 1)
		FROM max_seq ms
		WHERE fc.tenant_id = ms.tenant_id AND fc.tipo = 'APARTADO'
	"""))


def next_seq(conn: Connection, tenant_id: int, tipo: str) -> int:
	row = conn.execute(text("""
		UPDATE folio_counters
		SET next_seq = next_seq + 1
		WHERE tenant_id = :tenant_id AND tipo = :tipo
		RETURNING next_seq - 1 AS current_seq
	"""), {"tenant_id": tenant_id, "tipo": tipo}).fetchone()
	if not row:
		raise RuntimeError(f"No folio counter for tenant {tenant_id} tipo {tipo}")
	return int(row[0])


def format_folio(prefix: str, suc_code: str, seq: int) -> str:
	return f"{prefix}-{suc_code}-{str(seq).zfill(6)}"


def migrate_credit_sales_to_apartados(conn: Connection, tenant_slugs: Dict[int, str]) -> None:
	# Fetch credit sales
	rows = conn.execute(text("""
		SELECT s.*
		FROM sales s
		WHERE s.tipo_venta = 'credito'
	""")).mappings().all()

	for s in rows:
		tenant_id = s["tenant_id"]
		slug = tenant_slugs.get(tenant_id, str(tenant_id))
		seq = next_seq(conn, tenant_id=tenant_id, tipo="APARTADO")
		folio = format_folio("AP", slug, seq)

		# Insert apartado
		ap_row = conn.execute(text("""
			INSERT INTO apartados (
				tenant_id, user_id, folio_apartado,
				subtotal, discount_amount, tax_rate, tax_amount, total, created_at,
				vendedor_id, utilidad, total_cost,
				customer_name, customer_phone, customer_address, amount_paid, credit_status,
				legacy_sale_id, legacy_folio
			) VALUES (
				:s_tenant_id, :s_user_id, :folio,
				:subtotal, :discount_amount, :tax_rate, :tax_amount, :total, :created_at,
				:vendedor_id, :utilidad, :total_cost,
				:customer_name, :customer_phone, :customer_address, :amount_paid, :credit_status,
				:legacy_sale_id, :legacy_folio
			)
			RETURNING id
		"""), {
			"s_tenant_id": tenant_id,
			"s_user_id": s["user_id"],
			"folio": folio,
			"subtotal": s["subtotal"] or 0,
			"discount_amount": s["discount_amount"] or 0,
			"tax_rate": s["tax_rate"] or 0,
			"tax_amount": s["tax_amount"] or 0,
			"total": s["total"] or 0,
			"created_at": s["created_at"],
			"vendedor_id": s["vendedor_id"],
			"utilidad": s["utilidad"],
			"total_cost": s["total_cost"],
			"customer_name": s["customer_name"],
			"customer_phone": s["customer_phone"],
			"customer_address": s["customer_address"],
			"amount_paid": s["amount_paid"] or 0,
			"credit_status": s["credit_status"],
			"legacy_sale_id": s["id"],
			"legacy_folio": s.get("folio_apartado"),
		}).fetchone()
		apartado_id = int(ap_row[0])

		# Insert items
		items = conn.execute(text("""
			SELECT *
			FROM sale_items
			WHERE sale_id = :sale_id
		"""), {"sale_id": s["id"]}).mappings().all()
		for it in items:
			conn.execute(text("""
				INSERT INTO apartado_items (
					apartado_id, product_id, name, codigo,
					quantity, unit_price, discount_pct, discount_amount, total_price,
					product_snapshot
				)
				VALUES (
					:apartado_id, :product_id, :name, :codigo,
					:quantity, :unit_price, :discount_pct, :discount_amount, :total_price,
					:product_snapshot
				)
			"""), {
				"apartado_id": apartado_id,
				"product_id": it["product_id"],
				"name": it["name"],
				"codigo": it["codigo"],
				"quantity": it["quantity"],
				"unit_price": it["unit_price"],
				"discount_pct": it["discount_pct"],
				"discount_amount": it["discount_amount"],
				"total_price": it["total_price"],
				"product_snapshot": it["product_snapshot"],
			})


def assign_folios_to_contado_sales(conn: Connection, tenant_slugs: Dict[int, str]) -> None:
	rows = conn.execute(text("""
		SELECT id, tenant_id
		FROM sales
		WHERE (tipo_venta = 'contado' OR tipo_venta IS NULL)
		  AND (folio_venta IS NULL OR folio_venta = '')
	""")).fetchall()

	for sale_id, tenant_id in rows:
		seq = next_seq(conn, tenant_id=tenant_id, tipo="VENTA")
		slug = tenant_slugs.get(tenant_id, str(tenant_id))
		folio = format_folio("V", slug, seq)
		conn.execute(text("""
			UPDATE sales
			SET folio_venta = :folio
			WHERE id = :sale_id
		"""), {"folio": folio, "sale_id": sale_id})


def run():
	engine: Engine = create_engine(settings.database_url)
	with engine.begin() as conn:
		tenant_slugs = get_tenant_slugs(conn)
		ensure_counters(conn)
		migrate_credit_sales_to_apartados(conn, tenant_slugs)
		assign_folios_to_contado_sales(conn, tenant_slugs)
	print("✅ Migración de apartados y asignación de folios completada")


if __name__ == "__main__":
	run()


