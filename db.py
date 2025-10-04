import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="tamproxgen",
        user="postgres",
        password="postgres",
        cursor_factory=RealDictCursor  # to return dict instead of tuple
    )
    return conn
