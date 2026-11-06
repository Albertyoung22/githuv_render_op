import os
import sys
import socket
import threading
import webbrowser
import time

try:
    import customtkinter as ctk
except ImportError:
    import tkinter as ctk
    print("Warning: customtkinter not found, falling back to standard tkinter")

try:
    import qrcode
    from PIL import Image, ImageTk
    HAS_QR = True
except ImportError:
    HAS_QR = False

try:
    import webview
    HAS_WEBVIEW = True
except ImportError:
    HAS_WEBVIEW = False

from app import app, play_audio_on_speaker, generate_speech_bytes, HAS_PYGAME, HAS_EDGE_TTS
from waitress import serve
import asyncio
import pygame

PORT = 10000

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class DesktopControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.lan_ip = get_lan_ip()
        self.local_url = f"http://127.0.0.1:{PORT}"
        self.lan_url = f"http://{self.lan_ip}:{PORT}"

        self.title("GitHub & Render 沉浸式教學 - 桌面控制中心 (Desktop App)")
        self.geometry("980x700")
        self.minsize(880, 620)

        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Start Waitress server in background thread
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()

        self.setup_ui()

    def run_server(self):
        print(f"[Waitress] Starting server on 0.0.0.0:{PORT}...")
        serve(app, host='0.0.0.0', port=PORT, threads=6)

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        # Top Banner
        top_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#1e1b4b", border_width=1, border_color="#4338ca")
        top_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 12), sticky="ew")

        # Top Banner Logo & Title
        title_box = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_box.pack(side="left", padx=16, pady=10)

        logo_png_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_png_path):
            try:
                pil_logo = Image.open(logo_png_path).convert("RGB")
                self.logo_ctk = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(38, 38))
                logo_lbl = ctk.CTkLabel(title_box, image=self.logo_ctk, text="")
                logo_lbl.pack(side="left", padx=(0, 10))
            except Exception:
                pass

        title_lbl = ctk.CTkLabel(
            title_box,
            text="GitHub & Render 部署教學 — 桌面應用程式",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff"
        )
        title_lbl.pack(side="left")

        status_pill = ctk.CTkLabel(
            top_frame,
            text="● Waitress 伺服器運行中 (Port 10000)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#46e3b7",
            fg_color="#064e3b",
            corner_radius=20,
            padx=14,
            pady=6
        )
        status_pill.pack(side="right", padx=20, pady=14)

        # Left Column
        left_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#0f172a")
        left_frame.grid(row=1, column=0, padx=(20, 10), pady=(0, 15), sticky="nsew")

        # Card 1: Localhost
        c1 = ctk.CTkFrame(left_frame, corner_radius=10, fg_color="#1e293b", border_width=1, border_color="#334155")
        c1.pack(fill="x", padx=16, pady=(14, 8))

        c1_title = ctk.CTkLabel(c1, text="🏠 本機訪問網址 (Localhost)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#f8fafc")
        c1_title.pack(anchor="w", padx=14, pady=(10, 2))

        c1_url = ctk.CTkEntry(c1, font=ctk.CTkFont(family="Consolas", size=13), height=32)
        c1_url.insert(0, self.local_url)
        c1_url.configure(state="readonly")
        c1_url.pack(fill="x", padx=14, pady=4)

        c1_btn_box = ctk.CTkFrame(c1, fg_color="transparent")
        c1_btn_box.pack(fill="x", padx=14, pady=(4, 10))

        b1_open = ctk.CTkButton(
            c1_btn_box,
            text="🌐 開啟本機網頁 (預設瀏覽器)",
            command=lambda: webbrowser.open(self.local_url),
            fg_color="#4f46e5",
            hover_color="#4338ca",
            height=32
        )
        b1_open.pack(side="left", fill="x", expand=True, padx=(0, 6))

        b1_copy = ctk.CTkButton(
            c1_btn_box,
            text="📋 複製",
            width=70,
            command=lambda: self.copy_to_clipboard(self.local_url, b1_copy),
            fg_color="#334155",
            hover_color="#475569",
            height=32
        )
        b1_copy.pack(side="right")

        # Card 2: LAN IP
        c2 = ctk.CTkFrame(left_frame, corner_radius=10, fg_color="#1e293b", border_width=1, border_color="#334155")
        c2.pack(fill="x", padx=16, pady=8)

        c2_title = ctk.CTkLabel(c2, text="🌐 本機區域網路 IP 訪問 (LAN IP)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#38bdf8")
        c2_title.pack(anchor="w", padx=14, pady=(10, 2))

        c2_url = ctk.CTkEntry(c2, font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), height=32, text_color="#38bdf8")
        c2_url.insert(0, self.lan_url)
        c2_url.configure(state="readonly")
        c2_url.pack(fill="x", padx=14, pady=4)

        c2_btn_box = ctk.CTkFrame(c2, fg_color="transparent")
        c2_btn_box.pack(fill="x", padx=14, pady=(4, 10))

        b2_open = ctk.CTkButton(
            c2_btn_box,
            text="🌐 開啟區網 IP 網頁",
            command=lambda: webbrowser.open(self.lan_url),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=32
        )
        b2_open.pack(side="left", fill="x", expand=True, padx=(0, 6))

        b2_copy = ctk.CTkButton(
            c2_btn_box,
            text="📋 複製",
            width=70,
            command=lambda: self.copy_to_clipboard(self.lan_url, b2_copy),
            fg_color="#334155",
            hover_color="#475569",
            height=32
        )
        b2_copy.pack(side="right")

        # Card 3: Native Window (PyWebView)
        c3 = ctk.CTkFrame(left_frame, corner_radius=10, fg_color="#1e293b", border_width=1, border_color="#334155")
        c3.pack(fill="x", padx=16, pady=8)

        c3_title = ctk.CTkLabel(c3, text="🖥️ 獨立原生桌面視窗 (Desktop Native Window)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#a7f3d0")
        c3_title.pack(anchor="w", padx=14, pady=(10, 2))

        b3_webview = ctk.CTkButton(
            c3,
            text="🚀 啟動獨立原生桌面視窗",
            command=self.open_webview_window,
            fg_color="#059669",
            hover_color="#047857",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=34
        )
        b3_webview.pack(fill="x", padx=14, pady=(4, 10))

        # Card 4: Direct Speaker Sound Controller (RelayBell Style)
        c4 = ctk.CTkFrame(left_frame, corner_radius=10, fg_color="#172554", border_width=1, border_color="#1d4ed8")
        c4.pack(fill="x", padx=16, pady=(8, 14))

        c4_title = ctk.CTkLabel(c4, text="🔊 電腦喇叭直出語音測試 (RelayBell 廣播架構)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#93c5fd")
        c4_title.pack(anchor="w", padx=14, pady=(10, 2))

        # Phrase selection
        self.phrase_var = ctk.StringVar(value="歡迎使用 GitHub 與 Render 沉浸式語音系統！")
        phrase_menu = ctk.CTkOptionMenu(
            c4,
            values=[
                "歡迎使用 GitHub 與 Render 沉浸式語音系統！",
                "步驟一：安裝 Git 與設定使用者身分",
                "步驟二：專案結構與 Dockerfile 容器化配置",
                "步驟三：在 GitHub 建立儲存庫並執行 Git Push",
                "步驟四：在 Render 授權綁定 GitHub 儲存庫",
                "步驟五：建立 Web Service 並綁定 0.0.0.0 與動態 PORT",
                "🎉 恭喜！服務已成功上線運行！"
            ],
            variable=self.phrase_var,
            height=32,
            fg_color="#1e293b"
        )
        phrase_menu.pack(fill="x", padx=14, pady=4)

        # Voice Selector & Play/Stop Buttons
        c4_ctrl_box = ctk.CTkFrame(c4, fg_color="transparent")
        c4_ctrl_box.pack(fill="x", padx=14, pady=(4, 10))

        self.voice_var = ctk.StringVar(value="zh-TW-HsiaoChenNeural")
        voice_dropdown = ctk.CTkOptionMenu(
            c4_ctrl_box,
            values=[
                "zh-TW-HsiaoChenNeural",
                "zh-TW-YunJheNeural",
                "zh-CN-XiaoxiaoNeural",
                "zh-CN-YunxiNeural"
            ],
            variable=self.voice_var,
            width=180,
            height=32,
            fg_color="#1e293b"
        )
        voice_dropdown.pack(side="left", padx=(0, 6))

        self.btn_speak_speaker = ctk.CTkButton(
            c4_ctrl_box,
            text="🔊 喇叭直接發聲",
            command=self.speak_on_speaker,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            height=32
        )
        self.btn_speak_speaker.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_stop_speaker = ctk.CTkButton(
            c4_ctrl_box,
            text="⏹️ 停止",
            width=65,
            command=self.stop_speaker,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            height=32
        )
        btn_stop_speaker.pack(side="right")

        # Right Column
        right_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#0f172a")
        right_frame.grid(row=1, column=1, padx=(10, 20), pady=(0, 15), sticky="nsew")

        qr_title = ctk.CTkLabel(right_frame, text="📱 手機掃碼直接瀏覽 (同 Wi-Fi)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f8fafc")
        qr_title.pack(padx=16, pady=(16, 4))

        if HAS_QR:
            try:
                qr = qrcode.QRCode(box_size=4, border=2)
                qr.add_data(self.lan_url)
                qr.make(fit=True)
                qr_raw = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
                pil_img = qr_raw.get_image().convert("RGB")
                self.qr_photo = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(160, 160))
                
                qr_label = ctk.CTkLabel(right_frame, image=self.qr_photo, text="")
                qr_label.pack(pady=4)
            except Exception as e:
                qr_label = ctk.CTkLabel(right_frame, text="[QR 產生失敗]", text_color="#94a3b8")
                qr_label.pack(pady=40)
        else:
            qr_label = ctk.CTkLabel(right_frame, text="[QR 模組未安裝]", text_color="#94a3b8")
            qr_label.pack(pady=40)

        qr_sub = ctk.CTkLabel(
            right_frame,
            text=f"掃描後在手機體驗 Edge-TTS\n擬真神經語音與完整互動教學",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        )
        qr_sub.pack(pady=(0, 8))

        # Status & Info Box
        info_box = ctk.CTkFrame(right_frame, fg_color="#1e293b", corner_radius=10, border_width=1, border_color="#334155")
        info_box.pack(fill="x", padx=16, pady=8)

        info_text = (
            "📌 伺服器與語音規格：\n"
            "• 核心架構：Flask + Waitress WSGI\n"
            "• 語音協議：Microsoft Edge-TTS (Token v2)\n"
            "• 音量增強：+50% Volume Boost\n"
            f"• 監聽位址：0.0.0.0:{PORT}\n"
            f"• 區網 IP：{self.lan_ip}"
        )
        info_lbl = ctk.CTkLabel(info_box, text=info_text, font=ctk.CTkFont(family="Consolas", size=11), justify="left", text_color="#cbd5e1")
        info_lbl.pack(padx=12, pady=10, anchor="w")

        # Speaker Playback Log status
        self.speaker_status_lbl = ctk.CTkLabel(
            right_frame,
            text="🔊 喇叭狀態：閒置中",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94a3b8"
        )
        self.speaker_status_lbl.pack(pady=(6, 12))

    def copy_to_clipboard(self, text, button):
        self.clipboard_clear()
        self.clipboard_append(text)
        original_text = button.cget("text")
        button.configure(text="✓ 已複製！", fg_color="#059669")
        self.after(1500, lambda: button.configure(text=original_text, fg_color="#334155"))

    def speak_on_speaker(self):
        text = self.phrase_var.get().strip()
        voice = self.voice_var.get()

        def do_speak():
            self.speaker_status_lbl.configure(text="🎙️ 正在產生微軟 Edge 語音...", text_color="#38bdf8")
            self.btn_speak_speaker.configure(state="disabled")
            try:
                audio_bytes = asyncio.run(generate_speech_bytes(text, voice))
                self.speaker_status_lbl.configure(text="🔊 電腦喇叭正在發聲播放...", text_color="#46e3b7")
                play_audio_on_speaker(audio_bytes)
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                self.speaker_status_lbl.configure(text="✓ 播放完成！", text_color="#46e3b7")
                time.sleep(1.5)
                self.speaker_status_lbl.configure(text="🔊 喇叭狀態：閒置中", text_color="#94a3b8")
            except Exception as e:
                self.speaker_status_lbl.configure(text=f"❌ 錯誤: {e}", text_color="#ef4444")
            finally:
                self.btn_speak_speaker.configure(state="normal")

        threading.Thread(target=do_speak, daemon=True).start()

    def stop_speaker(self):
        if HAS_PYGAME and pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.speaker_status_lbl.configure(text="⏹️ 已停止播放", text_color="#eab308")

    def open_webview_window(self):
        if not HAS_WEBVIEW:
            webbrowser.open(self.local_url)
            return

        def run_view():
            try:
                window = webview.create_window(
                    title="GitHub & Render 沉浸式互動手冊 - Desktop App",
                    url=self.local_url,
                    width=1200,
                    height=800,
                    min_size=(900, 600)
                )
                webview.start()
            except Exception as e:
                print("Webview error, falling back to browser:", e)
                webbrowser.open(self.local_url)

        threading.Thread(target=run_view, daemon=True).start()

def main():
    app = DesktopControlApp()
    app.mainloop()

if __name__ == '__main__':
    main()
