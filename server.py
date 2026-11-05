import os
from app import app
from waitress import serve

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Waitress WSGI Server running Flask on 0.0.0.0:{port}...")
    serve(app, host='0.0.0.0', port=port, threads=6)
