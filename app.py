import os
import socket
import asyncio
from flask import Flask, request, Response, jsonify, send_from_directory
from waitress import serve

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

app = Flask(__name__, static_folder='.', static_url_path='')

# In-memory cache for audio snippets
TTS_CACHE = {}

def get_lan_ip():
    """Detect local network LAN IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/status')
def status():
    port = int(os.environ.get('PORT', 10000))
    lan_ip = get_lan_ip()
    return jsonify({
        "status": "online",
        "framework": "Flask",
        "wsgi_server": "Waitress",
        "edge_tts": HAS_EDGE_TTS,
        "port": port,
        "localhost_url": f"http://127.0.0.1:{port}",
        "lan_url": f"http://{lan_ip}:{port}"
    })

@app.route('/api/info')
def info():
    port = int(os.environ.get('PORT', 10000))
    lan_ip = get_lan_ip()
    return jsonify({
        "lan_ip": lan_ip,
        "port": port,
        "localhost_url": f"http://127.0.0.1:{port}",
        "lan_url": f"http://{lan_ip}:{port}"
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
    lan_ip = get_lan_ip()
    print("=" * 60)
    print("🚀 Starting Flask Web App on Waitress WSGI Server")
    print(f"📡 Localhost URL: http://127.0.0.1:{port}")
    print(f"🌐 LAN Local IP:  http://{lan_ip}:{port}")
    print(f"🎙️ Edge-TTS:      {'Enabled' if HAS_EDGE_TTS else 'Disabled'}")
    print("=" * 60)
    serve(app, host='0.0.0.0', port=port, threads=6)
