CREATE TABLE IF NOT EXISTS guaymallen_catalog.bronze.api_meta (
    extract_id BIGINT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY COMMENT 'Primaty Key. Autogenerada Incremental.',
    endpoint_called STRING COMMENT 'Nodo del Graph API consultado. Ej: /{ig-user-id}/media',
    parameters_used STRING COMMENT 'Parametros de la URL. CRÍTICO en Meta: aquí se guardan los "fields" solicitados (ej: fields=id,caption,insights)',
    raw_payload STRING COMMENT 'JSON completo de respuesta. Contiene la estructura anidada de data y paging (cursores)',
    status_code INT COMMENT 'Código de respuesta HTTP (200=OK, 400=Token Error, 403=Permisos)',
    extraction_timestamp TIMESTAMP COMMENT 'Momento exacto de la extracción (UTC)',
    extraction_date DATE GENERATED ALWAYS AS (CAST(extraction_timestamp AS DATE)) COMMENT 'Columna virtual para optimizar el filtrado por fecha'
)
USING DELTA
PARTITIONED BY (extraction_date)
COMMENT 'Tabla Bronze (Raw) para datos provenientes de Meta Graph API (Instagram/Facebook).'
;