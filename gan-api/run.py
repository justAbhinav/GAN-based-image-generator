import uvicorn
from pyngrok import ngrok
import webbrowser

if __name__ == "__main__":
    # Start the FastAPI server
    public_url = ngrok.connect(8000).public_url
    print(f"\nPublic URL: {public_url}")
    print("Share this URL with your audience!")
    print("Press Ctrl+C to stop the server\n")
    
    # Open the URL in the default browser
    webbrowser.open(public_url)
    
    # Run the server
    uvicorn.run(
        "server:app",  # Use import string format for reload to work
        host="0.0.0.0",  # This makes the server accessible from other devices on the network
        port=8000,
        reload=True  # Enable auto-reload for development
    ) 