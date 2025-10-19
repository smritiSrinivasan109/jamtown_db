import os
import streamlit as st
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from pgvector.psycopg import register_vector
import psycopg
import google.generativeai as genai
from dotenv import load_dotenv
import textwrap

# -------------------- CONFIG --------------------
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("PGDATABASE", "jamtown_db")
PGUSER = os.getenv("PGUSER", "smritisrinivasan")
PGPASSWORD = os.getenv("PGPASSWORD", "")
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
GEN_MODEL = "models/gemini-2.5-flash"
VECTOR_DIM = 1536

# -------------------- HELPERS --------------------
def ensure_vector_extension():
    """Ensure pgvector extension is active in the current database."""
    with psycopg.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD or None,
        sslmode="require",
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()

def get_connection():
    db_uri = os.getenv("DATABASE_URL") or (
        f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}?sslmode=require"
    )
    conn = psycopg.connect(db_uri)
    register_vector(conn)


def encode_texts(model, texts):
    if isinstance(texts, str):
        texts = [texts]
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    if embeddings.shape[1] < VECTOR_DIM:
        embeddings = np.pad(embeddings, ((0, 0), (0, VECTOR_DIM - embeddings.shape[1])), mode="constant")
    return embeddings

def search_similar(conn, model, query, limit=5):
    embedding = encode_texts(model, query)[0].tolist()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                name,
                genre,
                location,
                nonprofit_interests,
                passion_statement,
                bio,
                social_links,
                passion_embedding <=> (%s)::vector AS distance
            FROM artists
            ORDER BY passion_embedding <=> (%s)::vector
            LIMIT %s
            """,
            (embedding, embedding, limit),
        )
        return cur.fetchall()

def make_prompt(query, artist_rows):
    artist_blocks = []
    for r in artist_rows:
        name, genre, location, npi, passion, bio, socials, dist = r
        entry = f"""Name: {name}
Genre: {genre}
Location: {location}
Nonprofit Interest: {npi}
Bio: {bio}
Reasoning: {passion}
"""
        artist_blocks.append(entry.strip())
    artists_text = "\n---\n".join(artist_blocks)
    prompt = f"""
You are helping match musicians with nonprofit organizations
based on their bios and stated nonprofit interests.

Question: {query}

Here are some artist bios and interests:
{artists_text}

If the question is unrelated to the artists' interests, say so clearly.
Otherwise, return the names of artists most relevant to the cause and the reasoning behind your decision.
"""
    return prompt.strip()

def format_prompt_preview(prompt):
    lines = []
    for line in prompt.strip().split("\n"):
        if line.startswith("Question:"):
            lines.append(f"**Question:** {line.replace('Question:', '').strip()}\n")
        elif line.startswith("Here are some artist"):
            lines.append(f"---\n### Retrieved Artist Bios\n")
        elif line.strip().startswith("Name:"):
            lines.append(f"**{line.strip()}**  ")
        elif line.strip().startswith("Genre:") or line.strip().startswith("Location:"):
            lines.append(f"{line.strip()}  ")
        elif line.strip().startswith("Nonprofit Interest:"):
            lines.append(f"*{line.strip()}*  ")
        elif line.strip().startswith("Bio:") or line.strip().startswith("Reasoning:"):
            wrapped = textwrap.fill(line.strip(), width=100)
            lines.append(f"{wrapped}\n")
        else:
            lines.append(line)
    return "\n".join(lines)

# -------------------- STREAMLIT UI --------------------
st.set_page_config(page_title="Artist–Nonprofit Matcher", layout="wide")
st.title("Jamtown AI: Artist–Nonprofit Matcher")

st.write("Enter a cause or description to find artists who align with it.")

query = st.text_input("Example: 'Looking for artists supporting environmental conservation'")
limit = st.slider("Number of artists to retrieve", 3, 10, 5)

if st.button("Find Matching Artists") and query:
    with st.spinner("Searching database and generating reasoning..."):
        try:
            ensure_vector_extension()  # ensure pgvector is loaded
            model = SentenceTransformer(MODEL_NAME)
            with get_connection() as conn:
                results = search_similar(conn, model, query, limit)

            if not results:
                st.warning("No artists found for that query.")
            else:
                st.subheader("Retrieved Artists")
                for i, r in enumerate(results, start=1):
                    name, genre, location, npi, passion, bio, socials, dist = r
                    with st.expander(f"{i}. {name} ({genre}, {location}) — distance {dist:.3f}"):
                        st.markdown(f"**Genre:** {genre}")
                        st.markdown(f"**Location:** {location}")
                        st.markdown(f"**Nonprofit Interests:** {npi}")
                        st.markdown(f"**Passion Statement:** {passion}")
                        st.markdown(f"**Bio:** {bio}")
                        if socials:
                            st.markdown(f"**Socials:** {socials}")

                prompt = make_prompt(query, results)
                formatted = format_prompt_preview(prompt)

                st.markdown("---")
                st.markdown("## Gemini RAG Prompt")
                st.markdown(formatted)

                model_g = genai.GenerativeModel(GEN_MODEL)
                response = model_g.generate_content(prompt)

                st.markdown("---")
                st.markdown("## Recommendation")
                st.markdown(response.text.strip())

        except Exception as e:
            st.error(f"Error: {e}")
