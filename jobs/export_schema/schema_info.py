import csv
import io

from django.db import connection

from nautobot.apps.jobs import Job, register_jobs

SMALL_QUERY = """
    SET enable_nestloop = 0;
    SELECT
        'postgresql' AS dbms,
        t.table_catalog,
        t.table_schema,
        t.table_name,
        c.column_name,
        c.ordinal_position,
        c.data_type,
        c.character_maximum_length,
        n.constraint_type,
        k2.table_schema,
        k2.table_name,
        k2.column_name
    FROM information_schema.tables t
    NATURAL LEFT JOIN information_schema.columns c
    LEFT JOIN (
        information_schema.key_column_usage k
        NATURAL JOIN information_schema.table_constraints n
        NATURAL LEFT JOIN information_schema.referential_constraints r
    ) ON c.table_catalog = k.table_catalog
    AND c.table_schema = k.table_schema
    AND c.table_name = k.table_name
    AND c.column_name = k.column_name
    LEFT JOIN information_schema.key_column_usage k2
        ON k.position_in_unique_constraint = k2.ordinal_position
    AND r.unique_constraint_catalog = k2.constraint_catalog
    AND r.unique_constraint_schema = k2.constraint_schema
    AND r.unique_constraint_name = k2.constraint_name
    WHERE t.TABLE_TYPE = 'BASE TABLE'
    AND t.table_schema NOT IN ('information_schema', 'pg_catalog');
"""

LARGE_QUERY = """
    WITH base_offset AS (
        SELECT COALESCE(MAX(ordinal_position), 0) AS base FROM information_schema.columns
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
    ),
    customfield_info AS (
        SELECT
            'postgresql' AS dbms,
            'nautobot' AS table_catalog,
            'public' AS table_schema,
            CONCAT(dct.app_label, '_', dct.model) AS table_name,
            CONCAT('CF_', ecf.key) AS column_name,
            ROW_NUMBER() OVER (PARTITION BY dct.app_label, dct.model ORDER BY ecf.key) + bo.base AS ordinal_position,
            ecf.type AS data_type,
            CAST(NULL AS INTEGER) AS character_maximum_length,
            NULL AS constraint_type,
            NULL AS referenced_table_schema,
            NULL AS referenced_table_name,
            NULL AS referenced_column_name
        FROM extras_customfield ecf
        INNER JOIN extras_customfield_content_types ecct ON ecf.id = ecct.customfield_id
        INNER JOIN django_content_type dct ON ecct.contenttype_id = dct.id
        CROSS JOIN base_offset bo
    ),
    cf_count AS (
        SELECT MAX(ordinal_position) AS base FROM customfield_info
    ),
    customrelationship_info AS (
        SELECT
            'postgresql' AS dbms,
            'nautobot' AS table_catalog,
            'public' AS table_schema,
            CONCAT(src_ct.app_label, '_', src_ct.model) AS table_name,
            CONCAT('CR_', dest_ct.model, '_id') AS column_name,
            ROW_NUMBER() OVER (PARTITION BY src_ct.app_label, src_ct.model ORDER BY er.key) + cf.base AS ordinal_position,
            'uuid' AS data_type,
            CAST(NULL AS INTEGER) AS character_maximum_length,
            'FOREIGN KEY' AS constraint_type,
            'public' AS referenced_table_schema,
            CONCAT(dest_ct.app_label, '_', dest_ct.model) AS referenced_table_name,
            'id' AS referenced_column_name
        FROM extras_relationship er
        INNER JOIN django_content_type src_ct ON er.source_type_id = src_ct.id
        INNER JOIN django_content_type dest_ct ON er.destination_type_id = dest_ct.id
        CROSS JOIN cf_count cf
    ),
    schema_info AS (
        SELECT
            'postgresql' AS dbms,
            t.table_catalog,
            t.table_schema,
            t.table_name,
            c.column_name,
            c.ordinal_position,
            c.data_type,
            c.character_maximum_length,
            n.constraint_type,
            k2.table_schema AS referenced_table_schema,
            k2.table_name AS referenced_table_name,
            k2.column_name AS referenced_column_name
        FROM information_schema.tables t
        NATURAL LEFT JOIN information_schema.columns c
        LEFT JOIN (
            information_schema.key_column_usage k
            NATURAL JOIN information_schema.table_constraints n
            NATURAL LEFT JOIN information_schema.referential_constraints r
        ) ON c.table_catalog = k.table_catalog
        AND c.table_schema = k.table_schema
        AND c.table_name = k.table_name
        AND c.column_name = k.column_name
        LEFT JOIN information_schema.key_column_usage k2
        ON k.position_in_unique_constraint = k2.ordinal_position
        AND r.unique_constraint_catalog = k2.constraint_catalog
        AND r.unique_constraint_schema = k2.constraint_schema
        AND r.unique_constraint_name = k2.constraint_name
        WHERE t.TABLE_TYPE = 'BASE TABLE'
        AND t.table_schema NOT IN ('information_schema', 'pg_catalog')
    )
    SELECT * FROM schema_info
    UNION ALL
    SELECT * FROM customfield_info
    UNION ALL
    SELECT * FROM customrelationship_info;
"""


def get_schema_info_csv(preamble, query):
    with connection.cursor() as cursor:
        cursor.execute(preamble)
        cursor.execute(query)

        # Extract column names
        headers = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    # Use StringIO to create in-memory CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write headers and data
    writer.writerow(headers)
    writer.writerows(rows)

    # Return CSV string
    return output.getvalue()

class ExportDBSchemaToCSV(Job):
    """Job to export Nautobot database schema to CSV for use with Lucidchart."""

    class Meta:
        """Meta object for ExportDBSchemaToCSV."""
        name = "Export Nautobot DB Schema to CSV"
        description = "Export Nautobot database schema to CSV file for use with Lucidchart."
        commit_default = False
    
    def run(self, **kwargs):
        """Run the job."""
        csv_data = get_schema_info_csv(preamble=SMALL_QUERY, query=LARGE_QUERY)
        self.create_file("schema_info.csv", csv_data)

jobs = [ExportDBSchemaToCSV]
register_jobs(*jobs)
