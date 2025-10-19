import os
import pandas as pd
import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# ---------------- CONFIG ----------------
load_dotenv()
PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("PGDATABASE", "jamtown_db")
PGUSER = os.getenv("PGUSER", "smritisrinivasan")
PGPASSWORD = os.getenv("PGPASSWORD", "")
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
VECTOR_DIM = 1536
CSV_PATH = "artist_training_data.csv"

# ---------------- HELPERS ----------------
def get_connection():
    conn = psycopg.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD or None,
    )
    register_vector(conn)
    return conn

def encode_texts(model, texts):
    if isinstance(texts, str):
        texts = [texts]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    if embeddings.shape[1] < VECTOR_DIM:
        embeddings = np.pad(embeddings, ((0, 0), (0, VECTOR_DIM - embeddings.shape[1])), mode="constant")
    return embeddings

# ---------------- MAIN ----------------
df = pd.read_csv(CSV_PATH)
df = df.rename(columns={
    "artist_bio": "bio",
    "nonprofit_reasoning": "passion_statement",
    "nonprofit_interest": "nonprofit_interests"
})

def to_interest_list(val):
    if pd.isna(val):
        return None
    if isinstance(val, list):
        return [x for x in val if isinstance(x, str)]
    return [v.strip() for v in str(val).split(",") if v.strip()]

df["nonprofit_interests"] = df["nonprofit_interests"].apply(to_interest_list)

model = SentenceTransformer(MODEL_NAME)
df["combined_text"] = df.apply(
    lambda x: f"{x['name']}. {x['genre']}. {x['location']}. {x['bio']}. {x['passion_statement']}", axis=1
)
embeddings = encode_texts(model, df["combined_text"].tolist())

with get_connection() as conn:
    with conn.cursor() as cur:
        for i, row in df.iterrows():
            try:
                cur.execute(
                    """
                    INSERT INTO artists (
                        name, genre, location, nonprofit_interests,
                        passion_statement, bio, passion_embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING
                    """,
                    (
                        row["name"],
                        row["genre"],
                        row["location"],
                        row["nonprofit_interests"],
                        row["passion_statement"],
                        row["bio"],
                        embeddings[i].tolist(),
                    ),
                )
            except Exception as e:
                print("Skipping row due to:", e)
        conn.commit()

print(f"Inserted {len(df)} artists into PostgreSQL.")