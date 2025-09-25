-- enable pgvector for ai embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Artists Table
CREATE TABLE artists (
    artist_id SERIAL PRIMARY KEY, -- unique ID for each artist
    name TEXT NOT NULL, -- artist's name
    genre TEXT, -- music genre (rock, pop, jazz, etc.)
    location TEXT, -- region artist is based in
    rate_range TEXT, -- range (e.g. "$500–$1000 per show")
    availability TEXT, -- general availability
    nonprofit_interests TEXT[], -- multiple choice list of causes (e.g. ['Education','Climate','Medical Research'])
    
    passion_statement TEXT, -- free response
    passion_embedding VECTOR(1536), -- space for AI embeddings, currently OpenAI's text embedding
    
    bio TEXT, -- short bio
    bio_embedding VECTOR(1536), -- space for AI embeddings
    
    social_links JSONB -- social links (e.g. { "instagram": "url", "spotify": "url" })
);

CREATE TABLE artist_availability (
    availability_id SERIAL PRIMARY KEY, -- unique id for availability entry
    artist_id INT REFERENCES artists(artist_id) ON DELETE CASCADE, -- for. key to artist
    day_of_week TEXT CHECK (day_of_week IN 
        ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')
    ), -- which days of week
    start_time TIME, -- start time
    end_time TIME -- end time
);

-- Hosts Table
CREATE TABLE hosts (
    hosts_id SERIAL PRIMARY KEY, -- unique ID for each host
    name TEXT NOT NULL, -- organization name
    type TEXT, -- e.g. school, community org, medical research
    location TEXT, -- region/city
    
    mission_statement TEXT, -- free response mission/description
    mission_embedding VECTOR(1536), -- space for AI embeddings
    
    causes_supported TEXT[], -- multiple-choice list (e.g. ['Education','Climate'])
    budget_range TEXT, -- e.g. "<$1k", "$5k–$20k"
    
    contact_info JSONB -- contact field (e.g. { "email": "xyz@mail.com", "phone": "(000) 000-0000" })
);

-- Sponsors Table
CREATE TABLE sponsors (
    sponsor_id SERIAL PRIMARY KEY, -- unique ID for each sponsor
    name TEXT NOT NULL, -- sponsor name
    industry TEXT, -- sponsor industry/sector
    location TEXT, -- region/city
    
    values_statement TEXT, -- sponsor’s values / why they support music/nonprofits
    values_embedding VECTOR(1536), -- space for AI embeddings
    
    budget_range TEXT, -- expected contribution range (e.g. "<$5k", "$5k–$20k")
    preferred_causes TEXT[], -- multiple-choice interests (aligning with nonprofits/artists)
    
    contact_info JSONB -- contact field (e.g. { "email": "x", "linkedin": "y" })
);
