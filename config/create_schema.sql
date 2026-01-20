-- Crear el esquema Bronze (Hereda ubicación del catálogo)
CREATE SCHEMA IF NOT EXISTS guaymallen_catalog.bronze
    COMMENT 'Capa de Ingesta: Datos crudos de las fuentes (Raw Data)'
;

-- Crear el esquema Silver (Hereda ubicación del catálogo)
CREATE SCHEMA IF NOT EXISTS guaymallen_catalog.silver
    COMMENT 'Capa de Refinamiento: Datos estructurados, listos para su consumo.'
;

-- Crear el esquema Gold (Hereda ubicación del catálogo)
CREATE SCHEMA IF NOT EXISTS guaymallen_catalog.gold
    COMMENT 'Capa de Negocio: Tablas agregadas y modelos dimensionales listos para Reporting y Dashboards.'
;
