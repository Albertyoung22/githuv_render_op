import os
import asyncio
from flask import Flask, request, Response, jsonify, send_from_directory
from waitress import serve

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

app = Flask(__name__, static_folder='.', static_url_path='')

# In-memory cache for audio snippets to guarantee sub-second response
TTS_CACHE = {}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/status')
def status():
    return jsonify({
        "status": "online",
        "framework": "Flask",
        "wsgi_server": "Waitress",
        "edge_tts": HAS_EDGE_TTS,
        "port": int(os.environ.get('PORT', 10000))
    })

@app.route('/api/tts')
def tts():
    text = request.args.get('text', '').strip()
    voice = request.args.get('voice', 'zh-TW-HsiaoChenNeural').strip()

    if not text:
        return jsonify({"error": "Missing 'text' parameter"}), 400

    if not HAS_EDGE_TTS:
        return jsonify({"error": "edge-tts is not available"}), 501

    cache_key = f"{voice}:{text}"
    audio_data = TTS_CACHE.get(cache_key)

    if not audio_data:
        try:
            async def generate_speech():
                comm = edge_tts.Communicate(text, voice)
                chunks = []
                async for chunk in comm.stream():
                    if chunk['type'] == 'audio':
                        chunks.append(chunk['data'])
                return b''.join(chunks)

            # Generate audio in a dedicated event loop
            audio_data = asyncio.run(generate_speech())
            TTS_CACHE[cache_key] = audio_data
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return Response(
        audio_data,
        mimetype="audio/mpeg",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": "inline"
        }
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"==================================================")
    print(f"🚀 Starting Flask Web App on Waitress WSGI Server")
    print(f"📡 Host: 0.0.0.0 | Port: {port}")
    print(f"🎙️ Microsoft Edge-TTS: {'Enabled' if HAS_EDGE_TTS else 'Disabled'}")
    print(f"==================================================")
    serve(app, host='0.0.0.0', port=port, threads=6)
