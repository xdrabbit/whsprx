import os
import chromadb
from chromadb.types import Metadata
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from sentence_transformers import SentenceTransformer
import logging
import requests
import json
import uuid
import websockets
import asyncio
from fastapi.responses import StreamingResponse, FileResponse
from dotenv import load_dotenv
from elevenlabs import Voice
from elevenlabs.client import ElevenLabs
import base64
from pydantic import BaseModel
from thread_store import ThreadStore
from asset_manager import save_base64_image
from export_queue import ExportQueue

# --- 1. Application Setup ---

# Load environment variables from .env file
load_dotenv()

# ComfyUI server details
COMFYUI_URL = "http://192.168.0.45:8188"
COMFYUI_CLIENT_ID = str(uuid.uuid4())

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


# Initialize the ElevenLabs client
try:
    ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
    if not ELEVEN_API_KEY:
        logger.warning("ELEVEN_API_KEY not found in environment variables. Text-to-speech will be disabled.")
        eleven_client = None
    else:
        eleven_client = ElevenLabs(api_key=ELEVEN_API_KEY)
        logger.info("ElevenLabs client initialized.")
except Exception as e:
    logger.error(f"Failed to initialize ElevenLabs client: {e}")
    eleven_client = None


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
        metadatas: list[Metadata] = [{"source_filename": file.filename, "chunk_index": i} for i in range(len(chunks))]

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
    Queries the ChromaDB collection with a given text string and returns the top 5 results.
    Includes metadata (source filename) in the response.
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")

    try:
        logger.info(f"Received query: '{q}'")
        results = collection.query(
            query_texts=[q],
            n_results=5
        )
        
        # The query returns a dictionary with the results, including documents and metadatas
        # Each is a list of lists, one for each query. We only have one query.
        documents = results.get('documents')
        metadatas = results.get('metadatas')

        if not documents or not metadatas:
             return []

        # Combine the document with its metadata
        response_data = [
            {"document": doc, "metadata": meta}
            for doc, meta in zip(documents[0], metadatas[0])
        ]

        return response_data

    except Exception as e:
        logger.error(f"An error occurred during query processing: {e}")
        raise HTTPException(status_code=500, detail="Error processing query.")


@app.get("/api/ollama/models")
async def get_ollama_models():
    """
    Fetches the list of available models from the Ollama API.
    """
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags")
        response.raise_for_status()  # Raise an exception for bad status codes
        models_data = response.json()
        # We only need the model names for the dropdown
        model_names = [model["name"] for model in models_data.get("models", [])]
        return {"models": model_names}
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to Ollama API: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to Ollama API. Ensure Ollama is running.")
    except Exception as e:
        logger.error(f"An error occurred while fetching Ollama models: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch models from Ollama.")


@app.get("/api/comfyui/models")
def get_comfyui_models():
    """
    Fetches the list of available checkpoint models from ComfyUI server.
    """
    try:
        response = requests.get(f"{COMFYUI_URL}/models/checkpoints")
        response.raise_for_status()
        models = response.json()
        return {"models": models}
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not fetch models from ComfyUI: {e}")
        raise HTTPException(status_code=503, detail="Could not fetch models from ComfyUI server.")
    except Exception as e:
        logger.error(f"Error fetching ComfyUI models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {e}")


@app.post("/api/generate-image")
async def generate_image(prompt: str = Form(...), model: str = Form(...)):
    """
    Generates an image using ComfyUI based on a prompt and a selected model.
    """
    try:
        # 1. Load the base workflow
        with open("comfy_workflow.json", "r") as f:
            workflow = json.load(f)

        # 2. Modify the workflow with the user's prompt and model choice
        workflow["6"]["inputs"]["text"] = prompt
        workflow["4"]["inputs"]["ckpt_name"] = model

        # Log the workflow being sent
        logger.info(f"Sending the following workflow to ComfyUI:\n{json.dumps(workflow, indent=2)}")

        # 3. Queue the prompt with ComfyUI
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({"prompt": workflow, "client_id": COMFYUI_CLIENT_ID}).encode('utf-8')
        response = requests.post(f"{COMFYUI_URL}/prompt", data=data, headers=headers)
        response.raise_for_status()
        prompt_id = response.json()['prompt_id']
        
        # 4. Wait for the image to be generated via WebSocket
        async with websockets.connect(f"ws://{COMFYUI_URL.split('//')[1]}/ws?clientId={COMFYUI_CLIENT_ID}") as websocket:
            while True:
                out = await websocket.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    if message['type'] == 'executed' and message['data']['prompt_id'] == prompt_id:
                        # We have our image details
                        data = message['data']['output']['images'][0]
                        image_path = f"{data['subfolder']}/{data['filename']}"
                        
                        # 5. Fetch the generated image from the ComfyUI output directory
                        image_url = f"{COMFYUI_URL}/view?filename={data['filename']}&subfolder={data['subfolder']}&type={data['type']}"
                        image_response = requests.get(image_url, stream=True)
                        image_response.raise_for_status()
                        
                        # 6. Stream the image back to the client
                        return StreamingResponse(image_response.iter_content(1024), media_type=image_response.headers['Content-Type'])

    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"WebSocket connection to ComfyUI closed unexpectedly: {e}")
        raise HTTPException(status_code=503, detail="Lost connection to image generation server.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to ComfyUI API for image generation: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to ComfyUI API.")
    except Exception as e:
        logger.error(f"An error occurred during image generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {e}")


@app.post("/api/text-to-speech")
async def text_to_speech(text: str = Form(...), voice_id: str = Form(...)):
    """
    Converts text to speech using the ElevenLabs API and streams the audio back.
    """
    if not eleven_client:
        raise HTTPException(status_code=501, detail="Text-to-speech service is not configured.")

    if not text:
        raise HTTPException(status_code=400, detail="No text provided for speech synthesis.")

    try:
        # Use the text_to_speech.stream method
        audio_stream = eleven_client.text_to_speech.stream(
            text=text,
            voice_id=voice_id
        )

        # The stream from the client is an iterator of bytes, which is exactly what StreamingResponse needs.
        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    except Exception as e:
        logger.error(f"Error during text-to-speech generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {e}")


@app.get("/api/elevenlabs/voices")
async def get_elevenlabs_voices():
    """
    Fetches the list of available voices from the ElevenLabs API.
    """
    if not eleven_client:
        raise HTTPException(status_code=501, detail="Text-to-speech service is not configured.")
    
    try:
        # Fetch available voices from the API
        voices_response = eleven_client.voices.get_all()
        # The response contains a 'voices' attribute which is a list of Voice objects
        voice_list = [{"voice_id": voice.voice_id, "name": voice.name} for voice in voices_response.voices]
        return {"voices": voice_list}
    except Exception as e:
        logger.error(f"Could not fetch ElevenLabs voices: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch voices from ElevenLabs.")


@app.post("/query/rag")
async def query_rag(query: str = Form(...), model: str = Form(...)):
    """
    Performs Retrieval-Augmented Generation.
    1. Retrieves relevant document chunks from ChromaDB.
    2. Constructs a prompt with the user's query and the retrieved context.
    3. Sends the prompt to the selected Ollama model.
    4. Returns the model's response.
    """
    logger.info(f"Received RAG query: '{query}' with model: '{model}'")

    # 1. Retrieve context from ChromaDB
    try:
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
        documents = results.get('documents')
        if not documents or not documents[0]:
            return {"answer": "I couldn't find any relevant documents to answer your question.", "context": []}
        
        context_chunks = documents[0]
        context = "\\n\\n---\\n\\n".join(context_chunks)
        logger.info(f"Retrieved context: {context[:500]}...") # Log first 500 chars of context

    except Exception as e:
        logger.error(f"Error querying ChromaDB: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving documents from the database.")

    # 2. Construct the prompt
    prompt = f"""
    Based on the following context, please answer the user's question.
    If the context does not contain the answer, state that you cannot find the answer in the provided documents.

    Context:
    {context}

    ---
    User's Question: {query}
    """

    # 3. Send to Ollama
    try:
        ollama_response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False  # For now, we'll get the full response at once
            }
        )
        ollama_response.raise_for_status()
        
        answer = ollama_response.json().get("response", "No response from model.")
        logger.info(f"Ollama model '{model}' responded: {answer[:200]}...")

        return {"answer": answer, "context": context_chunks}

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to Ollama model '{model}': {e}")
        raise HTTPException(status_code=503, detail=f"Could not connect to Ollama model '{model}'.")
    except Exception as e:
        logger.error(f"An error occurred during RAG processing: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while generating the answer.")


@app.post("/api/generate-image-prompt")
async def generate_image_prompt(
    base_prompt: str = Form(...),
    artistic_direction: str = Form(...),
    model: str = Form(...)
):
    """
    Uses an LLM to generate a new, more descriptive image prompt based on a base text and artistic direction.
    Acts as an "AI Art Director".
    """
    logger.info(f"Generating new image prompt with model {model}...")

    # This is the "meta-prompt" that instructs the LLM on how to behave.
    meta_prompt = f"""
    You are an expert prompt engineer for a text-to-image AI. Your task is to take a base text and an artistic direction, and rewrite them into a single, highly descriptive, and visually rich prompt.

    - Combine the concepts from the base text and the artistic direction.
    - Enhance the prompt with vivid details, such as lighting, composition, and mood.
    - Do not include any conversational text, explanations, or quotation marks.
    - The output should be a single, continuous block of text ready to be fed into an image generation model.

    Base Text: "{base_prompt}"

    Artistic Direction: "{artistic_direction}"

    Generate the new, enhanced image prompt now:
    """

    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": model,
                "prompt": meta_prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        
        new_prompt = response.json().get("response", "").strip()
        logger.info(f"Generated new prompt: {new_prompt}")

        return {"new_prompt": new_prompt}

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to Ollama for prompt generation: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to Ollama to generate the image prompt.")
    except Exception as e:
        logger.error(f"An error occurred during image prompt generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate image prompt.")


# --- 4. PixVerse Video Generation ---
PIXVERSE_API_KEY = os.getenv("PIXVERSE_API_KEY")
PIXVERSE_API_URL = "https://app-api.pixverse.ai/openapi/v2"

@app.post("/api/pixverse/generate-video")
async def generate_pixverse_video(prompt: str = Form(...)):
    """
    Starts a text-to-video generation task with PixVerse.
    """
    if not PIXVERSE_API_KEY:
        raise HTTPException(status_code=501, detail="PixVerse API key is not configured.")

    trace_id = str(uuid.uuid4())
    headers = {
        "API-KEY": PIXVERSE_API_KEY,
        "Content-Type": "application/json",
        "Ai-trace-id": trace_id
    }
    payload = {
        "aspect_ratio": "16:9",
        "duration": 5,
        "model": "v5",
        "negative_prompt": "blurry, low quality, distorted",
        "prompt": prompt,
        "quality": "540p",
        "seed": 0
    }

    try:
        logger.info(f"Sending PixVerse text-to-video request with trace_id: {trace_id}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{PIXVERSE_API_URL}/video/text/generate", headers=headers, json=payload)
        
        # Log the full response for debugging
        logger.info(f"PixVerse Response Status: {response.status_code}")
        logger.info(f"PixVerse Response Body: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        
        if data.get("ErrCode") != 0:
            error_msg = data.get('ErrMsg', 'Unknown error')
            logger.error(f"PixVerse API Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PixVerse API Error: {error_msg}")
        
        video_id = data.get("Resp", {}).get("video_id")
        if not video_id:
            raise HTTPException(status_code=500, detail="PixVerse API did not return a video_id.")

        logger.info(f"Successfully created video generation task with video_id: {video_id}")
        return {"video_id": video_id}

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error from PixVerse API: {e}")
        logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
        raise HTTPException(status_code=503, detail=f"PixVerse API error: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to PixVerse API: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to PixVerse API.")
    except Exception as e:
        logger.error(f"An error occurred during PixVerse video generation initiation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start video generation: {e}")

@app.post("/api/pixverse/generate-video-from-image")
async def generate_pixverse_video_from_image(
    prompt: str = Form(...),
    image: UploadFile = File(...),
    duration: int = Form(5),
    model: str = Form("v4.5"),
    quality: str = Form("540p"),
    motion_mode: str = Form("normal"),
    camera_movement: str = Form(None),
    seed: int = Form(0)
):
    """
    Starts an image-to-video generation task with PixVerse.
    """
    if not PIXVERSE_API_KEY:
        raise HTTPException(status_code=501, detail="PixVerse API key is not configured.")

    trace_id = str(uuid.uuid4())
    
    try:
        # Step 1: Upload image to PixVerse to get an img_id
        upload_headers = {
            "API-KEY": PIXVERSE_API_KEY,
            "Ai-trace-id": trace_id
        }
        
        image_content = await image.read()
        filename = image.filename or "upload.jpg"
        content_type = image.content_type or "image/jpeg"
        
        files = {'image': (filename, image_content, content_type)}
        
        logger.info(f"Uploading image to PixVerse with trace_id: {trace_id}")
        upload_response = requests.post(f"{PIXVERSE_API_URL}/image/upload", headers=upload_headers, files=files)
        
        logger.info(f"Image Upload Response Status: {upload_response.status_code}")
        logger.info(f"Image Upload Response Body: {upload_response.text}")
        
        upload_response.raise_for_status()
        upload_data = upload_response.json()

        if upload_data.get("ErrCode") != 0:
            error_msg = upload_data.get('ErrMsg', 'Unknown error')
            logger.error(f"PixVerse Image Upload Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PixVerse Image Upload Error: {error_msg}")

        img_id = upload_data.get("Resp", {}).get("img_id")
        if not img_id:
            raise HTTPException(status_code=500, detail="PixVerse API did not return an img_id.")

        logger.info(f"Successfully uploaded image, received img_id: {img_id}")

        # Step 2: Use the img_id to generate the video
        generation_headers = {
            "API-KEY": PIXVERSE_API_KEY,
            "Content-Type": "application/json",
            "Ai-trace-id": trace_id
        }
        payload = {
            "duration": duration,
            "img_id": int(img_id),
            "model": model,
            "motion_mode": motion_mode,
            "negative_prompt": "blurry, low quality, distorted",
            "prompt": prompt,
            "quality": quality,
            "seed": seed
        }
        
        # Add camera_movement only if specified
        if camera_movement and camera_movement != "none":
            payload["camera_movement"] = camera_movement

        logger.info(f"Sending image-to-video request with payload: {json.dumps(payload, indent=2)}")
        response = requests.post(f"{PIXVERSE_API_URL}/video/img/generate", headers=generation_headers, json=payload)
        
        logger.info(f"Video Generation Response Status: {response.status_code}")
        logger.info(f"Video Generation Response Body: {response.text}")
        
        response.raise_for_status()
        data = response.json()

        if data.get("ErrCode") != 0:
            error_msg = data.get('ErrMsg', 'Unknown error')
            logger.error(f"PixVerse API Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PixVerse API Error: {error_msg}")
        
        video_id = data.get("Resp", {}).get("video_id")
        if not video_id:
            raise HTTPException(status_code=500, detail="PixVerse API did not return a video_id.")

        logger.info(f"Successfully created image-to-video task with video_id: {video_id}")
        return {"video_id": video_id}

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error from PixVerse API: {e}")
        logger.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
        raise HTTPException(status_code=503, detail=f"PixVerse API error: {str(e)}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to PixVerse API: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to PixVerse API.")
    except Exception as e:
        logger.error(f"An error occurred during PixVerse image-to-video generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start video generation: {e}")

@app.get("/api/pixverse/video-status/{video_id}")
async def get_pixverse_video_status(video_id: str):
    """
    Gets the status of a PixVerse video generation task.
    """
    if not PIXVERSE_API_KEY:
        raise HTTPException(status_code=501, detail="PixVerse API key is not configured.")

    headers = {
        "API-KEY": PIXVERSE_API_KEY,
        "Ai-trace-id": str(uuid.uuid4())
    }
    
    try:
        response = requests.get(f"{PIXVERSE_API_URL}/video/result/{video_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Status check for video_id {video_id}: {data}")

        if data.get("ErrCode") != 0:
            raise HTTPException(status_code=500, detail=f"PixVerse API Error: {data.get('ErrMsg')}")

        return data.get("Resp", {})

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to PixVerse API for status check: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to PixVerse API for status check.")
    except Exception as e:
        logger.error(f"An error occurred while checking PixVerse video status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check video status: {e}")

@app.get("/api/pixverse/credits")
async def get_pixverse_credits():
    """
    Gets the user's PixVerse credit balance.
    """
    if not PIXVERSE_API_KEY:
        raise HTTPException(status_code=501, detail="PixVerse API key is not configured.")

    headers = {
        "API-KEY": PIXVERSE_API_KEY,
        "ai-trace-id": str(uuid.uuid4())
    }
    
    try:
        response = requests.get(f"{PIXVERSE_API_URL}/account/balance", headers=headers)
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Credit balance check: {data}")

        if data.get("ErrCode") != 0:
            raise HTTPException(status_code=500, detail=f"PixVerse API Error: {data.get('ErrMsg')}")

        return data.get("Resp", {})

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to PixVerse API for credit check: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to PixVerse API for credit check.")
    except Exception as e:
        logger.error(f"An error occurred while checking PixVerse credits: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check credits: {e}")


@app.post("/api/pixverse/extend-video")
async def extend_pixverse_video(
    source_video_id: int = Form(...),
    prompt: str = Form(...),
    duration: int = Form(10),
    model: str = Form("v4.5"),
    quality: str = Form("540p"),
    motion_mode: str = Form("normal"),
    seed: int = Form(0)
):
    """
    Extends an existing PixVerse video.
    """
    if not PIXVERSE_API_KEY:
        raise HTTPException(status_code=501, detail="PixVerse API key is not configured.")

    trace_id = str(uuid.uuid4())
    headers = {
        "API-KEY": PIXVERSE_API_KEY,
        "Content-Type": "application/json",
        "Ai-trace-id": trace_id
    }
    
    payload = {
        "source_video_id": source_video_id,
        "prompt": prompt,
        "seed": seed,
        "quality": quality,
        "duration": duration,
        "model": model,
        "motion_mode": motion_mode
    }

    logger.info(f"Sending video extension request with trace_id: {trace_id}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(f"{PIXVERSE_API_URL}/video/extend/generate", headers=headers, json=payload)
        logger.info(f"PixVerse Extension Response Status: {response.status_code}")
        logger.info(f"PixVerse Extension Response Body: {response.text}")
        
        response.raise_for_status()
        data = response.json()

        if data.get("ErrCode") != 0:
            error_msg = data.get('ErrMsg', 'Unknown error')
            logger.error(f"PixVerse API Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PixVerse API Error: {error_msg}")
        
        video_id = data.get("Resp", {}).get("video_id")
        if not video_id:
            raise HTTPException(status_code=500, detail="PixVerse API did not return a video_id.")

        logger.info(f"Successfully extended video with new video_id: {video_id}")
        return {"video_id": video_id}

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to PixVerse API: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to PixVerse API.")
    except Exception as e:
        logger.error(f"An error occurred during video extension: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extend video: {e}")


@app.post("/api/pixverse/upload-media")
async def upload_pixverse_media(file: UploadFile = File(...)):
    """
    Uploads a video or audio file to PixVerse and returns media_id.
    """
    if not PIXVERSE_API_KEY:
        raise HTTPException(status_code=501, detail="PixVerse API key is not configured.")

    trace_id = str(uuid.uuid4())
    headers = {
        "API-KEY": PIXVERSE_API_KEY,
        "Ai-trace-id": trace_id
    }
    
    try:
        file_content = await file.read()
        filename = file.filename or "upload"
        content_type = file.content_type or "application/octet-stream"
        
        files = {'file': (filename, file_content, content_type)}
        
        logger.info(f"Uploading media to PixVerse with trace_id: {trace_id}")
        response = requests.post(f"{PIXVERSE_API_URL}/media/upload", headers=headers, files=files)
        
        logger.info(f"Media Upload Response Status: {response.status_code}")
        logger.info(f"Media Upload Response Body: {response.text}")
        
        response.raise_for_status()
        data = response.json()

        if data.get("ErrCode") != 0:
            error_msg = data.get('ErrMsg', 'Unknown error')
            logger.error(f"PixVerse Media Upload Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PixVerse Media Upload Error: {error_msg}")

        resp_data = data.get("Resp", {})
        logger.info(f"Successfully uploaded media: {resp_data}")
        return resp_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to PixVerse API: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to PixVerse API.")
    except Exception as e:
        logger.error(f"An error occurred during media upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload media: {e}")


@app.post("/api/pixverse/lip-sync")
async def generate_lip_sync(
    source_video_id: int = Form(...),
    lip_sync_tts_content: str = Form(None),
    lip_sync_tts_speaker_id: str = Form("auto"),
    audio_media_id: int = Form(None)
):
    """
    Generates lip-synced video using either TTS or uploaded audio.
    """
    if not PIXVERSE_API_KEY:
        raise HTTPException(status_code=501, detail="PixVerse API key is not configured.")

    if not lip_sync_tts_content and not audio_media_id:
        raise HTTPException(status_code=400, detail="Either lip_sync_tts_content or audio_media_id must be provided.")

    trace_id = str(uuid.uuid4())
    headers = {
        "API-KEY": PIXVERSE_API_KEY,
        "Content-Type": "application/json",
        "Ai-trace-id": trace_id
    }
    
    payload = {
        "source_video_id": source_video_id
    }
    
    # Add TTS parameters if text is provided
    if lip_sync_tts_content:
        payload["lip_sync_tts_content"] = lip_sync_tts_content
        payload["lip_sync_tts_speaker_id"] = lip_sync_tts_speaker_id
    
    # Add audio media ID if provided
    if audio_media_id:
        payload["audio_media_id"] = audio_media_id

    logger.info(f"Sending lip sync request with trace_id: {trace_id}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(f"{PIXVERSE_API_URL}/video/lip_sync/generate", headers=headers, json=payload)
        logger.info(f"PixVerse Lip Sync Response Status: {response.status_code}")
        logger.info(f"PixVerse Lip Sync Response Body: {response.text}")
        
        response.raise_for_status()
        data = response.json()

        if data.get("ErrCode") != 0:
            error_msg = data.get('ErrMsg', 'Unknown error')
            logger.error(f"PixVerse API Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PixVerse API Error: {error_msg}")
        
        video_id = data.get("Resp", {}).get("video_id")
        if not video_id:
            raise HTTPException(status_code=500, detail="PixVerse API did not return a video_id.")

        logger.info(f"Successfully created lip sync video with video_id: {video_id}")
        return {"video_id": video_id}

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to PixVerse API: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to PixVerse API.")
    except Exception as e:
        logger.error(f"An error occurred during lip sync generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate lip sync: {e}")


@app.get("/api/pixverse/tts-speakers")
async def get_tts_speakers(page_num: int = 1, page_size: int = 50):
    """
    Gets the list of available TTS speakers for lip sync.
    """
    if not PIXVERSE_API_KEY:
        raise HTTPException(status_code=501, detail="PixVerse API key is not configured.")

    trace_id = str(uuid.uuid4())
    headers = {
        "API-KEY": PIXVERSE_API_KEY,
        "Content-Type": "application/json",
        "Ai-trace-id": trace_id
    }
    
    try:
        response = requests.get(
            f"{PIXVERSE_API_URL}/video/lip_sync/tts_list",
            headers=headers,
            params={"page_num": page_num, "page_size": page_size}
        )
        logger.info(f"TTS Speakers Response Status: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()

        if data.get("ErrCode") != 0:
            error_msg = data.get('ErrMsg', 'Unknown error')
            logger.error(f"PixVerse API Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"PixVerse API Error: {error_msg}")

        return data.get("Resp", {})

    except requests.exceptions.RequestException as e:
        logger.error(f"Could not connect to PixVerse API: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to PixVerse API.")
    except Exception as e:
        logger.error(f"An error occurred while fetching TTS speakers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch TTS speakers: {e}")


# --- Image Chat with Vision Model ---
class ImageChatRequest(BaseModel):
    # Either provide `image_url` (http(s) URL) OR `image_base64` (base64-encoded image bytes).
    image_url: str | None = None
    image_base64: str | None = None
    message: str
    model: str = "llava:latest"  # Default to llava

@app.post("/api/chat-with-image")
async def chat_with_image(request: ImageChatRequest):
    """
    Chat with an AI about an image using Ollama vision models (llava/bakllava).
    Accepts image URL and user message, returns AI response.
    """
    try:
        # Determine where the image bytes come from: base64 provided already, or a URL to fetch
        image_base64 = None

        if request.image_base64:
            image_base64 = request.image_base64
        elif request.image_url:
            # Fetch the image and convert to base64
            try:
                img_response = requests.get(request.image_url, timeout=10)
            except Exception as e:
                logger.error(f"Failed to fetch image URL: {e}")
                raise HTTPException(status_code=400, detail="Failed to fetch image URL")

            if img_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch image")

            # Convert image to base64
            image_base64 = base64.b64encode(img_response.content).decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="No image provided. Include image_url or image_base64.")
        
        # Prepare Ollama vision request
        ollama_url = "http://127.0.0.1:11434/api/generate"
        payload = {
            "model": request.model,
            "prompt": request.message,
            "images": [image_base64],
            "stream": False
        }
        
        logger.info(f"Sending image chat request to Ollama with model: {request.model}")
        
        # Send to Ollama
        ollama_response = requests.post(ollama_url, json=payload, timeout=60)
        
        if ollama_response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Ollama error: {ollama_response.text}")
        
        result = ollama_response.json()
        ai_response = result.get("response", "")
        
        logger.info(f"Image chat response received: {ai_response[:100]}...")
        
        return {
            "response": ai_response,
            "model": request.model
        }
        
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timed out. Vision model may be loading.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to Ollama: {e}")
        raise HTTPException(status_code=503, detail="Could not connect to Ollama. Make sure it's running.")
    except HTTPException:
        # Re-raise HTTPExceptions so validation / bad-request errors keep their status codes
        raise
    except Exception as e:
        logger.error(f"Error in image chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- 6. Chat thread persistence (server-side) ---
# Initialize a thread store under the db directory
THREAD_STORE_PATH = os.path.join(DB_PATH, "chat_threads.json")
thread_store = ThreadStore(THREAD_STORE_PATH)

# export queue for async export jobs
export_queue = ExportQueue(DB_PATH, thread_store)


class CreateThreadRequest(BaseModel):
    name: str | None = None


class AddMessageRequest(BaseModel):
    role: str
    type: str | None = "text"
    text: str | None = None
    extra: dict | None = None


@app.get("/api/chat/threads")
async def list_threads():
    try:
        return {"threads": thread_store.list_threads()}
    except Exception as e:
        logger.error(f"Error listing threads: {e}")
        raise HTTPException(status_code=500, detail="Failed to list threads")


@app.post("/api/chat/threads")
async def create_thread(req: CreateThreadRequest):
    try:
        t = thread_store.create_thread(req.name)
        return t
    except Exception as e:
        logger.error(f"Error creating thread: {e}")
        raise HTTPException(status_code=500, detail="Failed to create thread")


@app.get("/api/chat/threads/{thread_id}")
async def get_thread(thread_id: str):
    try:
        t = thread_store.get_thread(thread_id)
        if not t:
            raise HTTPException(status_code=404, detail="Thread not found")
        return t
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching thread: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch thread")


@app.delete("/api/chat/threads/{thread_id}")
async def delete_thread(thread_id: str):
    try:
        ok = thread_store.delete_thread(thread_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Thread not found")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting thread: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete thread")


@app.post("/api/chat/threads/{thread_id}/messages")
async def add_message(thread_id: str, payload: AddMessageRequest):
    try:
        t = thread_store.get_thread(thread_id)
        if not t:
            raise HTTPException(status_code=404, detail="Thread not found")
        # Persist image contents to disk when present in payload.extra
        extra = payload.extra or {}
        if extra.get('image_base64'):
            # write to disk under DB_PATH/thread_assets/<thread_id>/
            dest_dir = os.path.join(DB_PATH, 'thread_assets', thread_id)
            file_path = save_base64_image(extra.get('image_base64'), dest_dir)
            if file_path:
                extra['file_path'] = file_path

        msg = thread_store.add_message(thread_id, role=payload.role, text=payload.text, type_=payload.type or "text", extra=extra)
        return msg
    except HTTPException:
        raise
    except KeyError:
        raise HTTPException(status_code=404, detail="Thread not found")
    except Exception as e:
        logger.error(f"Error adding message to thread: {e}")
        raise HTTPException(status_code=500, detail="Failed to add message")


@app.post("/api/chat/threads/{thread_id}/export")
async def export_thread(thread_id: str, format: str | None = 'zip'):
    """Enqueue an async export job (default: zip containing markdown + images).
    Returns job id which can be polled at /api/chat/threads/{thread_id}/export/{job_id}/status
    and the artifact can be downloaded at /api/chat/threads/{thread_id}/export/{job_id}/download
    """
    try:
        t = thread_store.get_thread(thread_id)
        if not t:
            raise HTTPException(status_code=404, detail="Thread not found")

        job = export_queue.enqueue(thread_id, format=format or 'zip')
        return {"job_id": job.id, "status": job.status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enqueuing export job: {e}")
        raise HTTPException(status_code=500, detail="Failed to enqueue export job")


@app.get("/api/chat/threads/{thread_id}/export/{job_id}/status")
async def export_status(thread_id: str, job_id: str):
    try:
        job = export_queue.status(job_id)
        if not job or job.thread_id != thread_id:
            raise HTTPException(status_code=404, detail="Export job not found")
        return {"job_id": job.id, "status": job.status, "error": job.error}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking export status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check export status")


@app.get("/api/chat/threads/{thread_id}/export/{job_id}/download")
async def export_download(thread_id: str, job_id: str):
    try:
        job = export_queue.status(job_id)
        if not job or job.thread_id != thread_id:
            raise HTTPException(status_code=404, detail="Export job not found")
        if job.status != 'done' or not job.result_path:
            raise HTTPException(status_code=409, detail=f"Export not ready: {job.status}")
        return FileResponse(job.result_path, media_type='application/zip', filename=os.path.basename(job.result_path))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve export")


# --- 5. Application Entry Point ---
@app.get("/")
async def read_main():
    return {"message": "Welcome to the FastAPI application!"}

# To run this application:
# 1. Make sure you have fastapi, uvicorn, python-multipart, chromadb, and sentence-transformers installed.
# 2. Run the command in your terminal: uvicorn main:app --reload
# 3. Open your browser to http://127.0.0.1:8000
