import tkinter as tk
from tkinter import ttk
import requests
import random
import threading
import time
from collections import deque

# --- AYARLAR ---
# Phyphox adresini buraya gir:
PHYPHOX_URL = "http://192.168.1.133/get?accX&accY&accZ" 
# HASSASİYET: 11.0 (Masa titreşimi için ideal, yerçekimi 9.8'in biraz üstü)
THRESHOLD = 11.0 

# --- AĞ KULLANICI TİPLERİ ---
users = [
    {"type": "ŞEHİR_İÇİ_ARAMA", "priority": 2},
    {"type": "ŞEHİR_DIŞI_ARAMA", "priority": 3}
]

class OperatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GSM Operatörü - Akıllı Afet Yönetim Paneli")
        self.root.geometry("900x700") # Ekranı biraz uzattık ki yeni göstergeler sığsın
        
        self.is_running = False
        self.thread = None
        
        # AI Filtresi için hafıza
        self.history = deque(maxlen=10)

        # --- YENİ SİMÜLASYON DEĞİŞKENLERİ ---
        self.total_users = 10000     # Toplam abone sayısı
        self.affected_count = 0      # Şu an afet modundaki kişi sayısı
        self.network_load = 35.0     # Başlangıç şebeke yükü (%)

        # 1. Üst Bilgi Paneli
        self.status_frame = tk.Frame(root, bg="gray", pady=15)
        self.status_frame.pack(fill="x")
        
        self.status_label = tk.Label(self.status_frame, text="SİSTEM BEKLEMEDE", font=("Arial", 18, "bold"), bg="gray", fg="white")
        self.status_label.pack()

        self.acc_label = tk.Label(self.status_frame, text="Sismik Veri: 0.00", font=("Arial", 12), bg="gray", fg="white")
        self.acc_label.pack()

        # --- YENİ EKLENEN KISIM: İSTATİSTİK PANELİ (DASHBOARD) ---
        self.stats_frame = tk.Frame(root, bg="#2c3e50", pady=15)
        self.stats_frame.pack(fill="x")

        # Sol taraf: Etkilenen Cihaz Sayısı
        self.lbl_users_title = tk.Label(self.stats_frame, text="AFET MODUNDAKİ CİHAZLAR", font=("Arial", 10), bg="#2c3e50", fg="white")
        self.lbl_users_title.pack()
        
        self.lbl_users_val = tk.Label(self.stats_frame, text="0 / 10,000", font=("Consolas", 24, "bold"), bg="#2c3e50", fg="#f1c40f")
        self.lbl_users_val.pack(pady=5)

        # Alt taraf: Şebeke Yoğunluğu
        self.lbl_load_title = tk.Label(self.stats_frame, text="ŞEBEKE YOĞUNLUĞU", font=("Arial", 10), bg="#2c3e50", fg="white")
        self.lbl_load_title.pack()

        # Progress Bar Stili (Yeşil/Kırmızı geçişi için)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("green.Horizontal.TProgressbar", foreground='green', background='green')
        self.style.configure("red.Horizontal.TProgressbar", foreground='red', background='red')

        self.pb_load = ttk.Progressbar(self.stats_frame, style="green.Horizontal.TProgressbar", orient="horizontal", length=400, mode="determinate")
        self.pb_load.pack(pady=5)
        
        self.lbl_load_val = tk.Label(self.stats_frame, text="%35 (Stabil)", font=("Arial", 12, "bold"), bg="#2c3e50", fg="#2ecc71")
        self.lbl_load_val.pack()
        # -----------------------------------------------------------

        # 2. Kontrol Butonları
        self.btn_frame = tk.Frame(root, pady=15)
        self.btn_frame.pack(fill="x")

        self.start_btn = tk.Button(self.btn_frame, text="▶ SİMÜLASYONU BAŞLAT", command=self.start_simulation, bg="green", fg="white", font=("Arial", 10, "bold"), width=25)
        self.start_btn.pack(side="left", padx=20)

        self.stop_btn = tk.Button(self.btn_frame, text="⏸ DURDUR", command=self.stop_simulation, state="disabled", bg="orange", fg="white", font=("Arial", 10, "bold"), width=15)
        self.stop_btn.pack(side="left", padx=20)

        self.exit_btn = tk.Button(self.btn_frame, text="❌ ÇIKIŞ", command=self.close_app, bg="darkred", fg="white", font=("Arial", 10, "bold"), width=10)
        self.exit_btn.pack(side="right", padx=20)

        # 3. Alt Panel (Liste)
        self.list_frame = tk.Frame(root, pady=10)
        self.list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(self.list_frame, columns=("Saat", "Kullanıcı", "Durum", "Kalite", "Süre"), show="headings", height=10)
        self.tree.heading("Saat", text="Zaman")
        self.tree.heading("Kullanıcı", text="Kullanıcı Tipi")
        self.tree.heading("Durum", text="Bağlantı Durumu")
        self.tree.heading("Kalite", text="Ses Kalitesi")
        self.tree.heading("Süre", text="Süre Limiti")
        
        self.tree.column("Saat", width=80, anchor="center")
        self.tree.column("Kullanıcı", width=150, anchor="center")
        self.tree.column("Durum", width=120, anchor="center")
        self.tree.column("Kalite", width=100, anchor="center")
        self.tree.column("Süre", width=100, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

    def start_simulation(self):
        if not self.is_running:
            self.is_running = True
            self.start_btn.config(state="disabled", bg="gray") 
            self.stop_btn.config(state="normal", bg="orange") 
            
            self.thread = threading.Thread(target=self.loop_simulation)
            self.thread.daemon = True
            self.thread.start()

    def stop_simulation(self):
        self.is_running = False
        self.start_btn.config(state="normal", bg="green")
        self.stop_btn.config(state="disabled", bg="gray")
        
        self.status_label.config(text="SİSTEM DURDURULDU", bg="gray")
        self.status_frame.config(bg="gray")
        self.acc_label.config(bg="gray", text="Veri akışı kesildi.")

    def close_app(self):
        self.is_running = False
        self.root.destroy()
        
    def update_ui(self, is_disaster, acceleration, call_log=None):
        if not self.is_running: return

        # --- YENİ EKLENEN SİMÜLASYON MATEMATİĞİ ---
        if is_disaster:
            # Afet anında:
            target_users = 8750  # Etkilenen kişi sayısı hızla artar
            target_load = 96.0   # Şebeke yükü %96'ya çıkar
            
            # Panel Renkleri (Kırmızı Alarm)
            self.status_frame.config(bg="red")
            self.status_label.config(text="🚨 AFET MODU (QoS AKTİF) 🚨", bg="red")
            self.acc_label.config(bg="red", text=f"Sismik Veri: {acceleration:.2f} (KRİTİK)")
            
            # Bar Rengi Kırmızı
            self.style.configure("red.Horizontal.TProgressbar", foreground='red', background='red')
            self.pb_load.configure(style="red.Horizontal.TProgressbar")
            self.lbl_load_val.config(text=f"%{int(self.network_load)} (AŞIRI YÜK)", fg="#e74c3c")
            self.lbl_users_val.config(fg="#e74c3c") # Yazıyı kırmızı yap

        else:
            # Normal anında:
            target_users = 0     # Etkilenen kimse yok
            target_load = 35.0   # Şebeke rahat (%35)
            
            # Panel Renkleri (Yeşil Normal)
            self.status_frame.config(bg="green")
            self.status_label.config(text="DURUM: NORMAL", bg="green")
            self.acc_label.config(bg="green", text=f"Sismik Veri: {acceleration:.2f}")

            # Bar Rengi Yeşil
            self.style.configure("green.Horizontal.TProgressbar", foreground='green', background='green')
            self.pb_load.configure(style="green.Horizontal.TProgressbar")
            self.lbl_load_val.config(text=f"%{int(self.network_load)} (Stabil)", fg="#2ecc71")
            self.lbl_users_val.config(fg="#f1c40f") # Yazıyı sarı yap

        # Yumuşak Geçiş Efekti (Sayılar birden zıplamasın, yavaş yavaş artsın)
        self.affected_count += (target_users - self.affected_count) * 0.1
        self.network_load += (target_load - self.network_load) * 0.05
        
        # Dalgalanma Efekti (Canlı gibi görünsün)
        self.network_load += random.uniform(-0.5, 0.5)

        # Değerleri Ekrana Yaz
        self.lbl_users_val.config(text=f"{int(self.affected_count):,} / {self.total_users:,}")
        self.pb_load['value'] = self.network_load
        # ----------------------------------------------------

        if call_log:
            timestamp = time.strftime("%H:%M:%S")
            self.tree.insert("", 0, values=(
                timestamp, 
                call_log["type"], 
                call_log["status"], 
                call_log["quality"],
                call_log["limit"]
            ))
            
            if len(self.tree.get_children()) > 15:
                self.tree.delete(self.tree.get_children()[-1])

    def loop_simulation(self):
        while self.is_running:
            acc = self.get_sensor_data()
            
            # AI Filtresi
            self.history.append(acc)
            avg_acc = sum(self.history) / len(self.history) if self.history else 9.8
            
            is_disaster = avg_acc > THRESHOLD
            
            caller = random.choice(users)
            call_result = {}
            
            if is_disaster:
                if caller["priority"] == 1:
                    call_result = {"type": caller["type"], "status": "BAĞLANDI ✅", "quality": "Yüksek (HD)", "limit": "Sınırsız"}
                elif caller["priority"] == 2:
                     call_result = {"type": caller["type"], "status": "BAĞLANDI ⚠️", "quality": "Standart", "limit": "Max 3dk"}
                elif caller["priority"] == 3:
                    call_result = {"type": caller["type"], "status": "KISITLI 📉", "quality": "Düşük (AMR)", "limit": "Max 60sn"}
            else: 
                call_result = {"type": caller["type"], "status": "BAĞLANDI", "quality": "Yüksek (HD)", "limit": "Sınırsız"}

            self.root.after(0, self.update_ui, is_disaster, avg_acc, call_result)
            time.sleep(0.1) 

    def get_sensor_data(self):
        try:
            response = requests.get(PHYPHOX_URL, timeout=0.5)
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
