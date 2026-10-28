# Data Architecture & Indexing

Name: data.md
description: Data schema, storage architecture, and indexing strategy for documentation.csv and local vector/graph storage.

## Dataset Overview
- **Source Dataset:** `documentation.csv` (764 metadata records).
- **Primary Schema:**
  - `id`: Unique document identifier (e.g., `P01`, `P02`).
  - `genre`: Category (e.g., `Press Release`, `First-person Field Account`).
  - `language`: Document language code (`en`, `fr`, etc.).

## Storage Strategy
- **Local Vectors:** ChromaDB / FAISS stored on local disk.
- **Graph Metadata:** Local JSON network file generated during preprocessing.