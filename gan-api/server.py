import io
import torch
import numpy as np
from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from model import MNISTGenerator, FashionMNISTGenerator
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()

# Mount static files for HTML frontend with cache disabled for development
app.mount("/static", StaticFiles(directory="static", html=True, check_dir=True), name="static")

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",")
)

# Add CORS middleware to handle cache headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add rate limit exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:;"
    
    if "/static/" in request.url.path:
        # Disable caching for static files during development
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Load models
def load_models():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load MNIST model
    mnist_model = MNISTGenerator().to(device)
    mnist_model.load_state_dict(torch.load(os.getenv("MODEL_PATH_MNIST", "models/mnist_digit_generator.pth"), map_location=device))
    mnist_model.eval()
    
    # Load Fashion MNIST model
    fashion_model = FashionMNISTGenerator().to(device)
    fashion_model.load_state_dict(torch.load(os.getenv("MODEL_PATH_FASHION", "models/mnist_fashion_generator.pth"), map_location=device))
    fashion_model.eval()
    
    return mnist_model, fashion_model, device

mnist_generator, fashion_generator, device = load_models()

def create_grid_image(generated_images, cell_padding=15, grid_spacing=8, image_size=200):
    try:
        cell_size = image_size + (cell_padding * 2)
        grid_width = (cell_size * 3) + (grid_spacing * 2)
        grid_height = (cell_size * 2) + grid_spacing
        grid_image = Image.new('L', (grid_width, grid_height), 'white')
        
        for idx, img_array in enumerate(generated_images):
            img_array = (img_array.transpose(1, 2, 0) * 127.5 + 127.5).astype(np.uint8)
            pil_img = Image.fromarray(img_array.squeeze(), mode="L")
            pil_img = pil_img.resize((image_size, image_size), Image.Resampling.LANCZOS)
            
            row = idx // 3
            col = idx % 3
            x = col * (cell_size + grid_spacing) + cell_padding
            y = row * (cell_size + grid_spacing) + cell_padding
            
            cell = Image.new('L', (cell_size, cell_size), 'white')
            border = Image.new('L', (cell_size, cell_size), 245)
            grid_image.paste(border, (x - cell_padding, y - cell_padding))
            grid_image.paste(cell, (x - cell_padding + 1, y - cell_padding + 1))
            grid_image.paste(pil_img, (x, y))
        
        img_bytes = io.BytesIO()
        grid_image.save(img_bytes, format="PNG", optimize=True)
        img_bytes.seek(0)
        logger.info(f"Created grid image of size: {len(img_bytes.getvalue())} bytes")
        return img_bytes
    except Exception as e:
        logger.error(f"Error creating grid image: {str(e)}")
        raise

@app.post("/generate/mnist")
@limiter.limit(os.getenv("RATE_LIMIT", "10/minute"))
async def generate_mnist(request: Request, digit: int = Form(..., ge=0, le=9)):
    try:
        logger.info(f"Generating MNIST images for digit: {digit}")
        z = torch.randn(6, 100).to(device)
        label = torch.tensor([digit] * 6, dtype=torch.long).to(device)
        
        with torch.no_grad():
            generated = mnist_generator(z, label).cpu().numpy()
        
        img_bytes = create_grid_image(generated)
        logger.info("Successfully generated MNIST images")
        
        response = StreamingResponse(img_bytes, media_type="image/png")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    except Exception as e:
        logger.error(f"Error generating MNIST images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/fashion")
@limiter.limit(os.getenv("RATE_LIMIT", "10/minute"))
async def generate_fashion(request: Request, class_id: int = Form(..., ge=0, le=9)):
    try:
        logger.info(f"Generating Fashion MNIST images for class: {class_id}")
        z = torch.randn(6, 100).to(device)
        label = torch.tensor([class_id] * 6, dtype=torch.long).to(device)
        
        with torch.no_grad():
            generated = fashion_generator(z, label).cpu().numpy()
        
        img_bytes = create_grid_image(generated)
        logger.info("Successfully generated Fashion MNIST images")
        
        response = StreamingResponse(img_bytes, media_type="image/png")
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    except Exception as e:
        logger.error(f"Error generating Fashion MNIST images: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with open(Path("static/index.html")) as f:
        return HTMLResponse(f.read())