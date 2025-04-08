"""
StepIn - Physical Meeting Platform

This script starts the FastAPI application.
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Start the application server"""
    port = int(os.getenv("PORT", 8000))
    
    # Start Uvicorn server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv("ENV", "development") == "development" else False,
        log_level="info"
    )

if __name__ == "__main__":
    main()