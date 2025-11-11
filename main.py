import os
import chromadb
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from sentence_transformers import SentenceTransformer
import logging

# --- 1. Application Setup ---

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastAPI application
app = FastAPI()

# Define the path for the persistent database
DB_PATH = "db"
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)

# Load the embedding model (this can take a moment)
logger.info("Loading sentence transformer model...")
try:
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load sentence transformer model: {e}")
    # Exit if the model can't be loaded, as the app is not functional without it.
    exit()


# Initialize the persistent ChromaDB client
try:
    client = chromadb.PersistentClient(path=DB_PATH)
    # Get or create the collection
    collection = client.get_or_create_collection(name="document_archives")
    logger.info("ChromaDB client initialized and collection is ready.")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB: {e}")
    # Exit if the database can't be initialized.
    exit()


# --- 2. Frontend Endpoint ---

@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    """
    Serves the main HTML frontend file.
    """
    try:
        with open("frontend.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="frontend.html not found.")


# --- 3. API Endpoints ---

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Handles file uploads, chunks the document, generates embeddings for each chunk,
    and stores them in ChromaDB.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name specified.")

    try:
        # Read the content of the uploaded file
        contents = await file.read()
        document_text = contents.decode('utf-8')

        # --- Chunking Logic ---
        # Split the document into chunks based on paragraphs (double newlines)
        # and filter out any empty chunks.
        chunks = [chunk.strip() for chunk in document_text.split('\n\n') if chunk.strip()]
        
        if not chunks:
            logger.info(f"File '{file.filename}' is empty or has no content to chunk.")
            return {"message": f"File '{file.filename}' has no processable content."}

        logger.info(f"Processing file: {file.filename}, split into {len(chunks)} chunks.")

        # Generate unique IDs and metadata for each chunk
        ids = [f"file_{file.filename}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source_filename": file.filename, "chunk_index": i} for i in range(len(chunks))]

        # Generate embeddings for each chunk
        embeddings = embedding_model.encode(chunks).tolist()

        # Add the chunks to the ChromaDB collection
        # Using 'upsert' is safer as it will update existing documents with the same ID.
        collection.upsert(
            embeddings=embeddings,
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )

        logger.info(f"Successfully ingested and indexed {len(chunks)} chunks from '{file.filename}'.")
        return {"message": f"Successfully ingested {len(chunks)} chunks from '{file.filename}'."}

    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")


@app.get("/query")
async def query_documents(q: str):
    """
    Performs a semantic search on the document collection.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' cannot be empty.")

    try:
        logger.info(f"Received query: '{q}'")
        # Generate embedding for the query
        query_embedding = embedding_model.encode([q]).tolist()

        # Query the collection
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=5  # Return the top 5 most relevant documents
        )

        return {"query": q, "results": results['documents'][0] if results and results['documents'] else []}

    except Exception as e:
        logger.error(f"Error during query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {e}")

# To run this application:
# 1. Make sure you have fastapi, uvicorn, python-multipart, chromadb, and sentence-transformers installed.
# 2. Run the command in your terminal: uvicorn main:app --reload
# 3. Open your browser to http://127.0.0.1:8000
