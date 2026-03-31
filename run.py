import os
import sys
import uvicorn

if __name__ == "__main__":
    # 1. Add 'backend' to the Python path so absolute imports work (import crud, import database)
    backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    sys.path.insert(0, backend_path)

    # 2. Get Railway port
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Railway app on port {port}")
    print("🌐 Binding to '0.0.0.0' (Standard IPv4) to allow Railway routing")
    
    # 3. Run the uvicorn server directly from Python
    # We use "main:app" because 'backend' is now in sys.path
    uvicorn.run("main:app", host="0.0.0.0", port=port)


