import psycopg2
import numpy as np
import pandas as pd

# data
df = pd.read_parquet("artist_embeddings.parquet")

# connect to postgres
conn = psycopg2.connect(
    dbname="jamtown_db",
    user="smritisrinivasan",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# insert each artist into db
for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO artist_embeddings (name, genre, location, nonprofit_interest, artist_bio, embedding)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        row['name'],
        row['genre'],
        row['location'],
        row['nonprofit_interest'],
        row['artist_bio'],
        np.array(row['embedding']).tolist()
    ))

conn.commit()
cur.close()
conn.close()

print("All embeddings inserted into PostgreSQL successfully.")
