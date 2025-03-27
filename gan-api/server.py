import io
import torch
import numpy as np
from fastapi import FastAPI, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from model import ConditionalGenerator
from pathlib import Path
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded

# limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

# Mount static files for HTML frontend with cache disabled for development
app.mount("/static", StaticFiles(directory="static", html=True, check_dir=True), name="static")

# Add CORS middleware to handle cache headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.middleware("http")
async def add_cache_control_header(request: Request, call_next):
    response = await call_next(request)
    if "/static/" in request.url.path:
        # Disable caching for static files during development
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Load model
def load_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = ConditionalGenerator().to(device)
    model.load_state_dict(torch.load("models/generator.pth", map_location=device))
    model.eval()
    return model, device

generator, device = load_model()

@app.post("/generate")
async def generate_image(digit: int = Form(..., ge=0, le=9)):
    # Generate random noise for 6 images
    z = torch.randn(6, 100).to(device)
    label = torch.tensor([digit] * 6, dtype=torch.long).to(device)
    
    # Generate images
    with torch.no_grad():
        generated = generator(z, label).cpu().numpy()
    
    # Create a grid of images with padding
    cell_padding = 15  # Reduced padding inside each cell
    grid_spacing = 8  # Reduced space between grid cells
    image_size = 200  # Base image size
    cell_size = image_size + (cell_padding * 2)  # Cell size including padding
    grid_width = (cell_size * 3) + (grid_spacing * 2)  # 3 columns with spacing
    grid_height = (cell_size * 2) + grid_spacing  # 2 rows with spacing
    grid_image = Image.new('L', (grid_width, grid_height), 'white')
    
    # Place each generated image in the grid
    for idx, img_array in enumerate(generated):
        # Convert to PIL Image
        img_array = (img_array.transpose(1, 2, 0) * 127.5 + 127.5).astype(np.uint8)
        pil_img = Image.fromarray(img_array.squeeze(), mode="L")
        # Resize the image to our desired size
        pil_img = pil_img.resize((image_size, image_size), Image.Resampling.LANCZOS)
        
        # Calculate position in grid with spacing
        row = idx // 3
        col = idx % 3
        x = col * (cell_size + grid_spacing) + cell_padding
        y = row * (cell_size + grid_spacing) + cell_padding
        
        # Create a cell background with border
        cell = Image.new('L', (cell_size, cell_size), 'white')
        # Draw border by creating a slightly darker background
        border = Image.new('L', (cell_size, cell_size), 245)  # Lighter border
        grid_image.paste(border, (x - cell_padding, y - cell_padding))
        grid_image.paste(cell, (x - cell_padding + 1, y - cell_padding + 1))  # Thinner border
        
        # Paste the actual image centered in the cell
        grid_image.paste(pil_img, (x, y))
    
    # Create in-memory bytes buffer
    img_bytes = io.BytesIO()
    grid_image.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    return StreamingResponse(img_bytes, media_type="image/png")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with open(Path("static/index.html")) as f:
        return HTMLResponse(f.read())