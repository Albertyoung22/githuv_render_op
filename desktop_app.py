import os
import sys
import socket
import threading
import webbrowser
import io
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

from app import app
from waitress import serve

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
        self.geometry("960x640")
        self.minsize(860, 560)

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Start Waitress server in background daemon thread
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()

        self.setup_ui()

    def run_server(self):
        print(f"[Waitress] Starting server on 0.0.0.0:{PORT}...")
        serve(app, host='0.0.0.0', port=PORT, threads=6)

    def setup_ui(self):
        # Configure layout
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        # Top Banner
        top_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#1e1b4b", border_width=1, border_color="#4338ca")
        top_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15), sticky="ew")

        title_lbl = ctk.CTkLabel(
            top_frame,
            text="🚀 GitHub & Render 部署教學 — 桌面應用程式",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff"
        )
        title_lbl.pack(side="left", padx=20, pady=16)

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
        status_pill.pack(side="right", padx=20, pady=16)

        # Left Column: Connection Cards
        left_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#0f172a")
        left_frame.grid(row=1, column=0, padx=(20, 10), pady=(0, 20), sticky="nsew")

        # Card 1: Localhost
        c1 = ctk.CTkFrame(left_frame, corner_radius=10, fg_color="#1e293b", border_width=1, border_color="#334155")
        c1.pack(fill="x", padx=16, pady=(16, 10))

        c1_title = ctk.CTkLabel(c1, text="🏠 本機訪問網址 (Localhost)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f8fafc")
        c1_title.pack(anchor="w", padx=14, pady=(12, 4))

        c1_url = ctk.CTkEntry(c1, font=ctk.CTkFont(family="Consolas", size=13), height=36)
        c1_url.insert(0, self.local_url)
        c1_url.configure(state="readonly")
        c1_url.pack(fill="x", padx=14, pady=6)

        c1_btn_box = ctk.CTkFrame(c1, fg_color="transparent")
        c1_btn_box.pack(fill="x", padx=14, pady=(4, 12))

        b1_open = ctk.CTkButton(
            c1_btn_box,
            text="🌐 開啟本機網頁 (預設瀏覽器)",
            command=lambda: webbrowser.open(self.local_url),
            fg_color="#4f46e5",
            hover_color="#4338ca",
            height=34
        )
        b1_open.pack(side="left", fill="x", expand=True, padx=(0, 6))

        b1_copy = ctk.CTkButton(
            c1_btn_box,
            text="📋 複製網址",
            width=90,
            command=lambda: self.copy_to_clipboard(self.local_url, b1_copy),
            fg_color="#334155",
            hover_color="#475569",
            height=34
        )
        b1_copy.pack(side="right")

        # Card 2: LAN IP
        c2 = ctk.CTkFrame(left_frame, corner_radius=10, fg_color="#1e293b", border_width=1, border_color="#334155")
        c2.pack(fill="x", padx=16, pady=10)

        c2_title = ctk.CTkLabel(c2, text="🌐 本機區域網路 IP 訪問 (LAN IP)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8")
        c2_title.pack(anchor="w", padx=14, pady=(12, 2))

        c2_desc = ctk.CTkLabel(c2, text="同一 Wi-Fi 下的手機、平板、其他電腦皆可直接輸入此網址瀏覽：", font=ctk.CTkFont(size=11), text_color="#94a3b8")
        c2_desc.pack(anchor="w", padx=14, pady=(0, 4))

        c2_url = ctk.CTkEntry(c2, font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), height=36, text_color="#38bdf8")
        c2_url.insert(0, self.lan_url)
        c2_url.configure(state="readonly")
        c2_url.pack(fill="x", padx=14, pady=6)

        c2_btn_box = ctk.CTkFrame(c2, fg_color="transparent")
        c2_btn_box.pack(fill="x", padx=14, pady=(4, 12))

        b2_open = ctk.CTkButton(
            c2_btn_box,
            text="🌐 開啟區網 IP 網頁",
            command=lambda: webbrowser.open(self.lan_url),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=34
        )
        b2_open.pack(side="left", fill="x", expand=True, padx=(0, 6))

        b2_copy = ctk.CTkButton(
            c2_btn_box,
            text="📋 複製網址",
            width=90,
            command=lambda: self.copy_to_clipboard(self.lan_url, b2_copy),
            fg_color="#334155",
            hover_color="#475569",
            height=34
        )
        b2_copy.pack(side="right")

        # Card 3: Native Window (PyWebView)
        c3 = ctk.CTkFrame(left_frame, corner_radius=10, fg_color="#1e293b", border_width=1, border_color="#334155")
        c3.pack(fill="x", padx=16, pady=(10, 16))

        c3_title = ctk.CTkLabel(c3, text="🖥️ 獨立原生桌面視窗 (Desktop Native Window)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#a7f3d0")
        c3_title.pack(anchor="w", padx=14, pady=(12, 2))

        c3_desc = ctk.CTkLabel(c3, text="以 Windows 獨立應用程式視窗呈現（無瀏覽器網址列干擾，完美沉浸體驗）：", font=ctk.CTkFont(size=11), text_color="#94a3b8")
        c3_desc.pack(anchor="w", padx=14, pady=(0, 6))

        b3_webview = ctk.CTkButton(
            c3,
            text="🚀 啟動獨立原生桌面視窗",
            command=self.open_webview_window,
            fg_color="#059669",
            hover_color="#047857",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38
        )
        b3_webview.pack(fill="x", padx=14, pady=(0, 14))

        # Right Column: QR Code & Server Info
        right_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="#0f172a")
        right_frame.grid(row=1, column=1, padx=(10, 20), pady=(0, 20), sticky="nsew")

        qr_title = ctk.CTkLabel(right_frame, text="📱 手機掃碼直接瀏覽 (同 Wi-Fi)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#f8fafc")
        qr_title.pack(padx=16, pady=(16, 6))

        # Generate QR Code image
        if HAS_QR:
            qr = qrcode.QRCode(box_size=4, border=2)
            qr.add_data(self.lan_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
            self.qr_photo = ctk.CTkImage(light_image=img, dark_image=img, size=(160, 160))
            
            qr_label = ctk.CTkLabel(right_frame, image=self.qr_photo, text="")
            qr_label.pack(pady=6)
        else:
            qr_label = ctk.CTkLabel(right_frame, text="[QR Code 模組載入中]", text_color="#94a3b8")
            qr_label.pack(pady=40)

        qr_sub = ctk.CTkLabel(
            right_frame,
            text=f"掃描後直接在手機體驗\nEdge-TTS 語音與互動教學",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        )
        qr_sub.pack(pady=(0, 10))

        # Server Information Box
        info_box = ctk.CTkFrame(right_frame, fg_color="#1e293b", corner_radius=10, border_width=1, border_color="#334155")
        info_box.pack(fill="x", padx=16, pady=10)

        info_text = (
            "📌 伺服器資訊：\n"
            "• 核心後端：Flask + Waitress WSGI\n"
            "• 語音引擎：Microsoft Edge-TTS\n"
            f"• 監聽 IP：0.0.0.0 (Port: {PORT})\n"
            f"• 區網 IP：{self.lan_ip}"
        )
        info_lbl = ctk.CTkLabel(info_box, text=info_text, font=ctk.CTkFont(family="Consolas", size=11), justify="left", text_color="#cbd5e1")
        info_lbl.pack(padx=12, pady=10, anchor="w")

    def copy_to_clipboard(self, text, button):
        self.clipboard_clear()
        self.clipboard_append(text)
        original_text = button.cget("text")
        button.configure(text="✓ 已複製！", fg_color="#059669")
        self.after(1500, lambda: button.configure(text=original_text, fg_color="#334155"))

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

        # Run in separate thread
        threading.Thread(target=run_view, daemon=True).start()

def main():
    app = DesktopControlApp()
    app.mainloop()

if __name__ == '__main__':
    main()
