import os
import sys
import asyncio
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

# Simple in-memory cache for generated TTS audio
TTS_CACHE = {}

class CustomHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local testing
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/tts':
            query = urllib.parse.parse_qs(parsed.query)
            text = query.get('text', [''])[0].strip()
            voice = query.get('voice', ['zh-TW-HsiaoChenNeural'])[0].strip()

            if not text:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'{"error": "Text parameter is required"}')
                return

            if not HAS_EDGE_TTS:
                self.send_response(501)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(b'{"error": "edge-tts library not installed on server"}')
                return

            cache_key = f"{voice}:{text}"
            audio_data = TTS_CACHE.get(cache_key)

            if not audio_data:
                try:
                    async def generate():
                        communicate = edge_tts.Communicate(text, voice)
                        chunks = []
                        async for chunk in communicate.stream():
                            if chunk['type'] == 'audio':
                                chunks.append(chunk['data'])
                        return b''.join(chunks)

                    audio_data = asyncio.run(generate())
                    TTS_CACHE[cache_key] = audio_data
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f'{{"error": "{str(e)}"}}'.encode('utf-8'))
                    return

            self.send_response(200)
            self.send_header('Content-Type', 'audio/mpeg')
            self.send_header('Content-Length', str(len(audio_data)))
            self.end_headers()
            self.wfile.write(audio_data)
            return

        elif parsed.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            status = '{"status": "online", "edge_tts": %s}' % ('true' if HAS_EDGE_TTS else 'false')
            self.wfile.write(status.encode('utf-8'))
            return

        # Serve static files as default
        super().do_GET()

def run_server():
    port = int(os.environ.get('PORT', 10000))
    server_address = ('0.0.0.0', port)
    httpd = ThreadingHTTPServer(server_address, CustomHandler)
    print(f"Server started on http://0.0.0.0:{port} (Edge-TTS: {'Enabled' if HAS_EDGE_TTS else 'Disabled'})")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
