Name: agents.md
description: Pipeline system architecture and AI agent definitions for document ingestion, vector indexing, and knowledge graph generation.

# AI Agents & Pipeline System Architecture

## 1. Document Ingestion Agent
- **Role:** Extracts text and structural metadata from Markdown and HTML/PDF source files.
- **Output:** Cleaned chunks with attached document IDs.

## 2. Vector Indexing Agent
- **Role:** Converts text chunks into embeddings using `all-MiniLM-L6-v2` and persists them locally.
- **Output:** Queryable vector index.

## 3. Knowledge Graph Agent
- **Role:** Builds connections (edges) between documents based on shared tags, genres, and semantic similarity.
- **Output:** Graph JSON structure for spiderweb UI visualization.