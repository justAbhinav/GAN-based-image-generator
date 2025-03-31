import uvicorn
from pyngrok import ngrok
import webbrowser
import qrcode
import os
from PIL import Image
import time

def generate_qr(url):
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add the URL to the QR code
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create an image from the QR Code
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Save the QR code image
    qr_path = "qr_code.png"
    qr_image.save(qr_path)
    return qr_path

if __name__ == "__main__":
    # Start the FastAPI server
    public_url = ngrok.connect(8000).public_url
    print(f"\nPublic URL: {public_url}")
    print("Press Ctrl+C to stop the server\n")
    
    # Generate and display QR code
    qr_path = generate_qr(public_url)
    print(f"QR Code has been generated and saved to: {qr_path}")
    
    # Open the URL in the default browser
    webbrowser.open(public_url)
    
    # Run the server
    uvicorn.run(
        "server:app",  # Use import string format for reload to work
        host="0.0.0.0",  # This makes the server accessible from other devices on the network
        port=8000,
        reload=True  # Enable auto-reload for development
    ) 