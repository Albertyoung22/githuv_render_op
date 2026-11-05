import os
import sys
import socket
import asyncio
import tempfile
import threading
from flask import Flask, request, Response, jsonify, send_from_directory
from waitress import serve

# 1. Edge-TTS Protocol Token Patch (Referenced from RelayBell)
try:
    import edge_tts
    import edge_tts.constants
    import edge_tts.communicate
    if hasattr(edge_tts.constants, "SEC_MS_GEC_VERSION") and str(edge_tts.constants.SEC_MS_GEC_VERSION).startswith("1-"):
        _new_sec_ver = str(edge_tts.constants.SEC_MS_GEC_VERSION).replace("1-", "2-", 1)
        edge_tts.constants.SEC_MS_GEC_VERSION = _new_sec_ver
        edge_tts.communicate.SEC_MS_GEC_VERSION = _new_sec_ver
        print(f"[EdgeTTS-Patch] 🛠️ 自動升級微軟協議權杖版本為: {_new_sec_ver}")
    HAS_EDGE_TTS = True
except Exception as _patch_err:
    try:
        import edge_tts
        HAS_EDGE_TTS = True
    except ImportError:
        HAS_EDGE_TTS = False

# 2. Pygame Sound Player (Referenced from RelayBell)
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except Exception:
    HAS_PYGAME = False

app = Flask(__name__, static_folder='.', static_url_path='')

# In-memory cache for audio snippets
TTS_CACHE = {}
PLAYBACK_LOCK = threading.Lock()

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

def play_audio_on_speaker(audio_data):
    """Play audio directly through PC soundcard/speakers (RelayBell style)"""
    if not HAS_PYGAME:
        return False
    with PLAYBACK_LOCK:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                fp.write(audio_data)
                tmp_path = fp.name
            
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            return True
        except Exception as e:
            print(f"[Speaker Playback Error] {e}")
            return False
        finally:
            # Clean up after playback in background thread
            def cleanup():
                import time
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                if tmp_path and os.path.exists(tmp_path):
                    try: os.remove(tmp_path)
                    except: pass
            threading.Thread(target=cleanup, daemon=True).start()

async def generate_speech_bytes(text, voice='zh-TW-HsiaoChenNeural', rate='+0%'):
    comm = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume='+50%')
    chunks = []
    async for chunk in comm.stream():
        if chunk['type'] == 'audio':
            chunks.append(chunk['data'])
    return b''.join(chunks)

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
        "speaker_audio": HAS_PYGAME,
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
        "lan_url": f"http://{lan_ip}:{port}",
        "speaker_available": HAS_PYGAME
    })

@app.route('/api/tts')
def tts():
    """Stream audio for web browsers"""
    text = request.args.get('text', '').strip()
    voice = request.args.get('voice', 'zh-TW-HsiaoChenNeural').strip()
    rate = request.args.get('rate', '+0%').strip()

    if not text:
        return jsonify({"error": "Missing 'text' parameter"}), 400

    if not HAS_EDGE_TTS:
        return jsonify({"error": "edge-tts is not available"}), 501

    cache_key = f"{voice}:{rate}:{text}"
    audio_data = TTS_CACHE.get(cache_key)

    if not audio_data:
        try:
            audio_data = asyncio.run(generate_speech_bytes(text, voice, rate))
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

@app.route('/api/speak', methods=['GET', 'POST'])
def speak():
    """Play audio directly on local computer speakers (RelayBell Broadcast Style)"""
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        text = data.get('text', '').strip()
        voice = data.get('voice', 'zh-TW-HsiaoChenNeural').strip()
    else:
        text = request.args.get('text', '').strip()
        voice = request.args.get('voice', 'zh-TW-HsiaoChenNeural').strip()

    if not text:
        return jsonify({"error": "Missing text parameter"}), 400

    cache_key = f"{voice}:+0%:{text}"
    audio_data = TTS_CACHE.get(cache_key)

    if not audio_data:
        try:
            audio_data = asyncio.run(generate_speech_bytes(text, voice))
            TTS_CACHE[cache_key] = audio_data
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    played = play_audio_on_speaker(audio_data)
    return jsonify({
        "success": True,
        "played_on_speaker": played,
        "text": text,
        "voice": voice
    })

@app.route('/api/stop_speak', methods=['POST', 'GET'])
def stop_speak():
    if HAS_PYGAME and pygame.mixer.get_init():
        pygame.mixer.music.stop()
    return jsonify({"success": True, "stopped": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    lan_ip = get_lan_ip()
    print("=" * 60)
    print("🚀 Starting Flask Web App on Waitress WSGI Server")
    print(f"📡 Localhost URL: http://127.0.0.1:{port}")
    print(f"🌐 LAN Local IP:  http://{lan_ip}:{port}")
    print(f"🎙️ Edge-TTS:      {'Enabled (with RelayBell Patch & Volume Boost)' if HAS_EDGE_TTS else 'Disabled'}")
    print(f"🔊 PC Speaker:    {'Available (pygame.mixer)' if HAS_PYGAME else 'Web-only'}")
    print("=" * 60)
    serve(app, host='0.0.0.0', port=port, threads=6)
