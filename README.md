# Jamtown Database Schema  

This repository contains the initial **PostgreSQL schema** for Jamtown’s backend. The schema is designed to store structured information about **artists, hosts, and sponsors**, with future support for AI-driven recommendations using embeddings (via `pgvector`).  

---

## Files  

- **`jamtown_schema.sql`**  
  Core schema file that defines all current tables.  
- *(future)* `mock_data.sql` → will include insert statements for sample artists, nonprofits, and sponsors.  
- *(future)* `queries.sql` → will demonstrate example searches and AI-assisted recommendations.  

---

## Current Tables  

### **Artists**  
Stores artist details including genre, location, rates, availability, and social links.  
- Text fields for **bio** and **passion statement**, with placeholders for **AI embeddings**.  

### **Artist Availability**  
Optional table for detailed weekly scheduling.  
- Captures day-of-week and start/end times linked to each artist.  

### **Hosts**  
Stores nonprofit organizations that may host fundraising events.  
- Includes mission statements and supported causes, with placeholder embeddings for future AI use.  

### **Sponsors**  
Stores sponsor information including industries, values, and contribution ranges.  
- Values statements are paired with embedding fields to enable AI-based alignment with causes.  

---

## Immediate Future Work  

- Add **join tables** (e.g., `events` or `bookings`) to connect artists, nonprofits, and sponsors.
- Insert **mock data** to test queries and search functionality.  
- Create **queries.sql** with examples of vector-based search and filtering.  

---

## Setup  

1. Make sure PostgreSQL is installed.  
2. Install the **pgvector extension**:  
    ```sql
    CREATE EXTENSION IF NOT EXISTS vector;
    ```
3. Run the schema:
    ```
    psql -U postgres -d jamtown -f jamtown_schema.sql
    ```