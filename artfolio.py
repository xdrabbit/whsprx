import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from datetime import datetime
import json
import uuid
from pathlib import Path
import shutil

app = FastAPI()

# Storage paths
STORAGE_DIR = Path("artfolio_storage")
GROUPS_DIR = STORAGE_DIR / "groups"
METADATA_FILE = STORAGE_DIR / "metadata.json"

# Initialize storage
STORAGE_DIR.mkdir(exist_ok=True)
GROUPS_DIR.mkdir(exist_ok=True)

def load_metadata():
    """Load metadata from JSON file"""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {"groups": {}}

def save_metadata(metadata):
    """Save metadata to JSON file"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

@app.get("/")
async def read_main():
    """Serve the main HTML page"""
    with open("artfolio.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/groups")
async def create_group(name: str = Form(...)):
    """Create a new art group"""
    metadata = load_metadata()
    
    # Check if group already exists
    if name in metadata["groups"]:
        raise HTTPException(status_code=400, detail="Group already exists")
    
    # Create group directory
    group_dir = GROUPS_DIR / name
    group_dir.mkdir(exist_ok=True)
    
    # Add to metadata
    metadata["groups"][name] = {
        "name": name,
        "created": datetime.now().isoformat(),
        "items": {}
    }
    save_metadata(metadata)
    
    return {"success": True, "group": name}

@app.get("/api/groups")
async def get_groups():
    """Get all groups"""
    metadata = load_metadata()
    return {"groups": list(metadata["groups"].keys())}

@app.get("/api/groups/{group_name}/items")
async def get_items(group_name: str):
    """Get all items in a group"""
    metadata = load_metadata()
    
    if group_name not in metadata["groups"]:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"items": list(metadata["groups"][group_name]["items"].keys())}

@app.post("/api/groups/{group_name}/items")
async def create_item(group_name: str, name: str = Form(...)):
    """Create a new item in a group"""
    metadata = load_metadata()
    
    if group_name not in metadata["groups"]:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if name in metadata["groups"][group_name]["items"]:
        raise HTTPException(status_code=400, detail="Item already exists")
    
    # Create item directory
    item_dir = GROUPS_DIR / group_name / name
    item_dir.mkdir(exist_ok=True)
    
    # Add to metadata
    metadata["groups"][group_name]["items"][name] = {
        "name": name,
        "created": datetime.now().isoformat(),
        "versions": []
    }
    save_metadata(metadata)
    
    return {"success": True, "item": name}

@app.get("/api/groups/{group_name}/items/{item_name}/versions")
async def get_versions(group_name: str, item_name: str):
    """Get all versions of an item"""
    metadata = load_metadata()
    
    if group_name not in metadata["groups"]:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if item_name not in metadata["groups"][group_name]["items"]:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"versions": metadata["groups"][group_name]["items"][item_name]["versions"]}

@app.post("/api/groups/{group_name}/items/{item_name}/versions")
async def upload_version(
    group_name: str,
    item_name: str,
    file: UploadFile = File(...)
):
    """Upload a new version of an item"""
    metadata = load_metadata()
    
    if group_name not in metadata["groups"]:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if item_name not in metadata["groups"][group_name]["items"]:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Generate version info
    timestamp = datetime.now()
    version_id = f"{timestamp.strftime('%Y%m%d%H%M%S')}_{file.filename}"
    
    # Save file
    item_dir = GROUPS_DIR / group_name / item_name
    file_path = item_dir / version_id
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Add to metadata
    version_data = {
        "id": version_id,
        "filename": file.filename,
        "uploaded": timestamp.isoformat(),
        "size": file_path.stat().st_size,
        "path": str(file_path.relative_to(STORAGE_DIR))
    }
    
    metadata["groups"][group_name]["items"][item_name]["versions"].append(version_data)
    save_metadata(metadata)
    
    return {"success": True, "version": version_data}

@app.get("/api/files/{group_name}/{item_name}/{version_id}")
async def get_file(group_name: str, item_name: str, version_id: str):
    """Get a specific version file"""
    file_path = GROUPS_DIR / group_name / item_name / version_id
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
