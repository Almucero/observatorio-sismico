import os

import psycopg


def connect():
    return psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ.get("POSTGRES_DB", "observatorio"),
        user=os.environ.get("POSTGRES_USER", "observatorio"),
        password=os.environ.get("POSTGRES_PASSWORD", "cambialo_en_local"),
    )
