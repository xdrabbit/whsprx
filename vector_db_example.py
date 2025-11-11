import chromadb
from sentence_transformers import SentenceTransformer

# --- 1. Setup ChromaDB and the Embedding Model ---

# Initialize ChromaDB. By default, it runs in-memory and is ephemeral.
# For persistence, you can configure it to save to disk:
client = chromadb.PersistentClient(path="/home/tkash/wsl_dev/whsprx/db")
client = chromadb.Client()

# Load a pre-trained sentence transformer model.
# This model is great for generating embeddings for sentences and paragraphs.
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# --- 2. Create a Collection ---

# A collection is where you'll store your documents, embeddings, and metadata.
# The get_or_create_collection method is idempotent, so you can run this
# script multiple times without creating duplicate collections.
collection = client.get_or_create_collection(name="document_archives")

# --- 3. Prepare and Add Documents ---

# Here is where you would load your actual documents.
# For this example, we'll use a small list of strings.
# Replace this with your logic to read from your archives (e.g., text files, PDFs).
documents = [
    "The Apollo 11 mission was the first to land humans on the Moon.",
    "The James Webb Space Telescope is the successor to the Hubble Space Telescope.",
    "Artificial intelligence is a branch of computer science.",
    "The first programmable computer was the Z1, created by Konrad Zuse.",
    "The history of space exploration is filled with incredible achievements."
]

# Generate embeddings for each document.
# The model.encode() method takes a list of strings and returns a list of vectors.
embeddings = embedding_model.encode(documents).tolist()

# Each document needs a unique ID. Here, we'll just use their index as a string.
ids = [f"doc_{i}" for i in range(len(documents))]

# Add the documents, their embeddings, and their IDs to the collection.
# This is the "indexing" step.
collection.add(
    embeddings=embeddings,
    documents=documents,
    ids=ids
)

print(f"Successfully added {len(documents)} documents to the collection.")

# --- 4. Perform a Semantic Search (Query) ---

# Now, let's ask a question. The database will find the documents
# that are most semantically similar to this query.
query_text = "What are some major milestones in space history?"

# First, generate an embedding for the query text itself.
query_embedding = embedding_model.encode([query_text]).tolist()

# Perform the query on the collection.
# We're asking for the top 2 most relevant results.
results = collection.query(
    query_embeddings=query_embedding,
    n_results=2
)

print("\n--- Query Results ---")
print(f"Query: '{query_text}'")
print("Most relevant documents:")
if results and results['documents']:
    for doc in results['documents'][0]:
        print(f"- {doc}")
else:
    print("No documents found.")

# --- Example of how to get all documents ---
# all_items = collection.get()
# print("\nAll items in collection:", all_items)
