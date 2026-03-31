import os
import uvicorn

if __name__ == "__main__":
    # Ensure we get the correct dynamically assigned PORT from Railway
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting Railway app on port {port}")
    print("🌐 Binding to '::' (Dual-stack IPv6/IPv4) strictly as required by Railway")
    
    # Run the uvicorn server directly from Python to bypass all shell wrapping bugs
    uvicorn.run("backend.main:app", host="::", port=port)
