CREATE VIEW DESCARGA_WORKBOOKS AS 
WITH PROYECTOS AS (
    -- Todos los proyectos (carpetas): forman el arbol
    SELECT
        ITEM_ID,
        ITEM_NAME,
        ITEM_PARENT_PROJECT_ID AS PARENT_ID
    FROM MDM_TABLEAU_SITE_CONTENT
    WHERE ITEM_TYPE = 'Project'
),
RUTAS_JERARQUICAS AS (
    -- Recorrido jerarquico: construye ruta completa de cada proyecto
    -- Incluyendo proyectos intermedios sin workbooks directos
    SELECT
        ITEM_ID,
        ITEM_NAME,
        PARENT_ID,
        LTRIM(SYS_CONNECT_BY_PATH(ITEM_NAME, '/'), '/') AS RUTA_COMPLETA,
        LEVEL AS PROFUNDIDAD
    FROM PROYECTOS
    START WITH PARENT_ID IS NULL          -- proyectos raiz
    CONNECT BY PRIOR ITEM_ID = PARENT_ID
)
 
-- ==========================================================
-- PARTE 1: WORKBOOKS (cada uno con su ruta completa)
-- ==========================================================
SELECT
    w.ITEM_LUID                                   AS WORKBOOK_LUID,
    w.ITEM_NAME                                   AS WORKBOOK,
    rj.RUTA_COMPLETA                              AS RUTA_PROYECTO,
    rj.RUTA_COMPLETA || '/' || w.ITEM_NAME        AS RUTA_LOCAL_DESTINO,
    w.OWNER_EMAIL,
    w.UPDATED_AT_LOC_HORA                         AS ULTIMA_ACTUALIZACION,
    'WORKBOOK'                                    AS TIPO_ITEM,
     w.ITEM_REVISION                              AS VERSION_ACTUAL,
    'SÍ'                                          AS DESCARGAR
FROM MDM_TABLEAU_SITE_CONTENT w
JOIN RUTAS_JERARQUICAS rj
  ON rj.ITEM_ID = w.ITEM_PARENT_PROJECT_ID
WHERE w.ITEM_TYPE = 'Workbook'
 
UNION ALL
 
-- ==========================================================
-- PARTE 2: CONTROL - Proyectos intermedios sin workbooks
-- ==========================================================
-- Esto te permite verificar que NINGUNA carpeta intermedia se pierde
SELECT
    NULL AS WORKBOOK_LUID,
    'N/A (carpeta intermedia)' AS WORKBOOK,
    rj.RUTA_COMPLETA AS RUTA_PROYECTO,
    rj.RUTA_COMPLETA AS RUTA_LOCAL_DESTINO,
    'N/A' AS OWNER_EMAIL,
    NULL AS ULTIMA_ACTUALIZACION,
    'CARPETA INTERMEDIA' AS TIPO_ITEM,
    NULL                              AS VERSION_ACTUAL,
    'Solo crear la carpeta' AS DESCARGAR
FROM RUTAS_JERARQUICAS rj
WHERE NOT EXISTS (
    -- Excluir si tiene workbooks DIRECTOS (ya salen en la PARTE 1)
    SELECT 1
    FROM MDM_TABLEAU_SITE_CONTENT w
    WHERE w.ITEM_TYPE = 'Workbook'
      AND w.ITEM_PARENT_PROJECT_ID = rj.ITEM_ID
)
 
ORDER BY RUTA_LOCAL_DESTINO, WORKBOOK, TIPO_ITEM;
