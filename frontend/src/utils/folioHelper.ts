/**
 * Helper functions for folio formatting
 */

/**
 * Limpia un folio removiendo el slug del tenant si existe
 * Ejemplo: "V-ANDANI-000001" -> "V-000001"
 *          "AP-ANDANI-000001" -> "AP-000001"
 *          "PED-ANDANI-000001" -> "PED-000001"
 *          "V-000001" -> "V-000001" (ya está limpio)
 */
export const cleanFolio = (folio: string | null | undefined): string => {
  if (!folio) return ''
  
  // Si el folio tiene formato PREFIX-SLUG-SEQ (3 partes separadas por guiones),
  // extraer solo PREFIX-SEQ
  const parts = folio.split('-')
  if (parts.length === 3) {
    // Formato: PREFIX-SLUG-SEQ -> PREFIX-SEQ
    // Ejemplo: "V-ANDANI-000001" -> "V-000001"
    return `${parts[0]}-${parts[2]}`
  }
  
  // Si ya está en formato correcto (PREFIX-SEQ) o es un fallback, devolverlo tal cual
  return folio
}

