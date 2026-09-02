import tkinter as tk
from tkinter import ttk
import requests
import random
import threading
import time

# --- AYARLAR ---
# Phyphox adresini buraya gir:
PHYPHOX_URL = "http://192.168.1.189/get?accX&accY&accZ" 
THRESHOLD = 15.0 # Telefon masada dururken çalışmasın diye yüksek tuttuk

# --- AĞ KULLANICI TİPLERİ ---
users = [
    {"type": "AFAD_YETKİLİSİ", "priority": 1},
    {"type": "AMBULANS_EKİBİ", "priority": 1},
    {"type": "SİVİL_VATANDAŞ", "priority": 2},     # Bölge halkı
    {"type": "ŞEHİR_DIŞI_ARAMA", "priority": 3}    # Merak eden akrabalar
]

class OperatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GSM Operatörü - Akıllı Afet Yönetim Paneli")
        self.root.geometry("800x600") # Geniş ekran
        
        self.is_running = False
        self.thread = None

        # 1. Üst Bilgi Paneli
        self.status_frame = tk.Frame(root, bg="gray", pady=20)
        self.status_frame.pack(fill="x")
        
        self.status_label = tk.Label(self.status_frame, text="SİSTEM BEKLEMEDE", font=("Arial", 20, "bold"), bg="gray", fg="white")
        self.status_label.pack()

        self.acc_label = tk.Label(self.status_frame, text="Sismik Veri: 0.00", font=("Arial", 12), bg="gray", fg="white")
        self.acc_label.pack()

        # 2. Kontrol Butonları (GERİ GELDİ!)
        self.btn_frame = tk.Frame(root, pady=15)
        self.btn_frame.pack(fill="x")

        # BAŞLAT
        self.start_btn = tk.Button(self.btn_frame, text="▶ SİMÜLASYONU BAŞLAT", command=self.start_simulation, bg="green", fg="white", font=("Arial", 10, "bold"), width=20)
        self.start_btn.pack(side="left", padx=20)

        # DURDUR (PAUSE)
        self.stop_btn = tk.Button(self.btn_frame, text="⏸ DURDUR", command=self.stop_simulation, state="disabled", bg="orange", fg="white", font=("Arial", 10, "bold"), width=15)
        self.stop_btn.pack(side="left", padx=20)

        # ÇIKIŞ
        self.exit_btn = tk.Button(self.btn_frame, text="❌ ÇIKIŞ", command=self.close_app, bg="darkred", fg="white", font=("Arial", 10, "bold"), width=10)
        self.exit_btn.pack(side="right", padx=20)

        # 3. Alt Panel (Arama Listesi - Detaylı)
        self.list_frame = tk.Frame(root, pady=10)
        self.list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(self.list_frame, columns=("Saat", "Kullanıcı", "Durum", "Kalite", "Süre"), show="headings", height=15)
        self.tree.heading("Saat", text="Zaman")
        self.tree.heading("Kullanıcı", text="Kullanıcı Tipi")
        self.tree.heading("Durum", text="Bağlantı Durumu")
        self.tree.heading("Kalite", text="Ses Kalitesi") # YENİ SÜTUN
        self.tree.heading("Süre", text="Süre Limiti")    # YENİ SÜTUN
        
        self.tree.column("Saat", width=80, anchor="center")
        self.tree.column("Kullanıcı", width=150, anchor="center")
        self.tree.column("Durum", width=120, anchor="center")
        self.tree.column("Kalite", width=100, anchor="center")
        self.tree.column("Süre", width=100, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

    def start_simulation(self):
        """Simülasyonu başlatır."""
        if not self.is_running:
            self.is_running = True
            self.start_btn.config(state="disabled", bg="gray") 
            self.stop_btn.config(state="normal", bg="orange") 
            
            # Yeni bir thread başlat
            self.thread = threading.Thread(target=self.loop_simulation)
            self.thread.daemon = True
            self.thread.start()

    def stop_simulation(self):
        """Simülasyonu durdurur."""
        self.is_running = False
        self.start_btn.config(state="normal", bg="green")
        self.stop_btn.config(state="disabled", bg="gray")
        
        # Arayüzü gri yap
        self.status_label.config(text="SİSTEM DURDURULDU", bg="gray")
        self.status_frame.config(bg="gray")
        self.acc_label.config(bg="gray", text="Veri akışı kesildi.")

    def close_app(self):
        """Uygulamayı kapatır."""
        self.is_running = False
        self.root.destroy()
        
    def update_ui(self, is_disaster, acceleration, call_log=None):
        if not self.is_running: return

        # Panel Renkleri
        if is_disaster:
            self.status_frame.config(bg="red")
            self.status_label.config(text="🚨 AFET MODU (QoS AKTİF) 🚨", bg="red")
            self.acc_label.config(bg="red", text=f"Sismik Veri: {acceleration:.2f} (KRİTİK)")
        else:
            self.status_frame.config(bg="green")
            self.status_label.config(text="DURUM: NORMAL", bg="green")
            self.acc_label.config(bg="green", text=f"Sismik Veri: {acceleration:.2f}")

        # Listeye Ekleme
        if call_log:
            timestamp = time.strftime("%H:%M:%S")
            self.tree.insert("", 0, values=(
                timestamp, 
                call_log["type"], 
                call_log["status"], 
                call_log["quality"],
                call_log["limit"]
            ))
            
            if len(self.tree.get_children()) > 20:
                self.tree.delete(self.tree.get_children()[-1])

    def loop_simulation(self):
        while self.is_running:
            acc = self.get_sensor_data()
            is_disaster = acc > THRESHOLD
            
            caller = random.choice(users)
            call_result = {}
            
            if is_disaster:
                # 1. ÖNCELİKLİ GRUP
                if caller["priority"] == 1:
                    call_result = {
                        "type": caller["type"], 
                        "status": "BAĞLANDI ✅", 
                        "quality": "Yüksek (HD)", 
                        "limit": "Sınırsız"
                    }
                # 2. BÖLGE HALKI
                elif caller["priority"] == 2:
                     call_result = {
                        "type": caller["type"], 
                        "status": "BAĞLANDI ⚠️", 
                        "quality": "Standart", 
                        "limit": "Max 3dk"
                    }
                # 3. ŞEHİR DIŞI (Senin İstediğin Özellik)
                elif caller["priority"] == 3:
                    call_result = {
                        "type": caller["type"], 
                        "status": "KISITLI 📉", 
                        "quality": "Düşük (AMR)", 
                        "limit": "Max 60sn"
                    }
            
            else: # NORMAL MOD
                call_result = {
                    "type": caller["type"], 
                    "status": "BAĞLANDI", 
                    "quality": "Yüksek (HD)", 
                    "limit": "Sınırsız"
                }

            self.root.after(0, self.update_ui, is_disaster, acc, call_result)
            time.sleep(0.8) # Akış hızı

    def get_sensor_data(self):
        try:
            response = requests.get(PHYPHOX_URL, timeout=1.0)
            data = response.json()
            ax = data["buffer"]["accX"]["buffer"][0]
            ay = data["buffer"]["accY"]["buffer"][0]
            az = data["buffer"]["accZ"]["buffer"][0]
            return (ax**2 + ay**2 + az**2) ** 0.5
        except:
            return 9.8 

if __name__ == "__main__":
    root = tk.Tk()
    app = OperatorApp(root)
    root.mainloop()
