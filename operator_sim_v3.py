import tkinter as tk
from tkinter import ttk
import requests
import random
import threading
import time
from collections import deque

# =========================
# AYARLAR
# =========================
PHYPHOX_URL = "http://192.168.1.178/get?accX&accY&accZ"
THRESHOLD = 11.0
MIN_TRIGGER_DEVICES = 1000
TOTAL_DEVICES = 10000
CONFIRMATION_CYCLES = 5  # Deprem moduna girmek için üst üste gereken tur sayısı

CALLER_TYPES = [
    {"type": "ACİL_YARDIM_EKİBİ", "priority": 1},
    {"type": "BÖLGEDEKİ_ABONE", "priority": 2},
    {"type": "ŞEHİR_DIŞI_ARAMA", "priority": 3}
]


class OperatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GSM Operatörü - Akıllı Afet Yönetim Paneli")
        self.root.geometry("980x780")

        self.is_running = False
        self.stop_event = threading.Event()
        self.thread = None

        self.history = deque(maxlen=10)

        self.confirm_counter = 0
        self.disaster_locked = False

        # Deprem modu süre sayacı
        self.disaster_start_time = None
        self.disaster_elapsed = 0

        self.total_devices = TOTAL_DEVICES
        self.critical_devices = 0
        self.network_load = 35.0
        self.sensor_ok = True

        # Geçici bağlantı kopmalarında hemen sensör yok demesin
        self.last_valid_acc = 9.8
        self.failed_reads = 0
        self.max_failed_reads = 5

        # =========================
        # ÜST PANEL
        # =========================
        self.status_frame = tk.Frame(root, bg="gray", pady=15)
        self.status_frame.pack(fill="x")

        self.status_label = tk.Label(
            self.status_frame,
            text="SİSTEM BEKLEMEDE",
            font=("Arial", 18, "bold"),
            bg="gray",
            fg="white"
        )
        self.status_label.pack()

        self.acc_label = tk.Label(
            self.status_frame,
            text="Referans Sismik Veri: 0.00",
            font=("Arial", 12),
            bg="gray",
            fg="white"
        )
        self.acc_label.pack()

        self.cluster_label = tk.Label(
            self.status_frame,
            text=f"Kritik veri gönderen cihaz: 0 / Eşik: {MIN_TRIGGER_DEVICES}",
            font=("Arial", 12, "bold"),
            bg="gray",
            fg="white"
        )
        self.cluster_label.pack()

        self.confirm_label = tk.Label(
            self.status_frame,
            text=f"Doğrulama: 0 / {CONFIRMATION_CYCLES}",
            font=("Arial", 11, "bold"),
            bg="gray",
            fg="white"
        )
        self.confirm_label.pack()

        # Yeni eklenen süre göstergesi
        self.duration_label = tk.Label(
            self.status_frame,
            text="Deprem Modu Süresi: 0 sn",
            font=("Arial", 11, "bold"),
            bg="gray",
            fg="white"
        )
        self.duration_label.pack()

        # =========================
        # İSTATİSTİK PANELİ
        # =========================
        self.stats_frame = tk.Frame(root, bg="#2c3e50", pady=15)
        self.stats_frame.pack(fill="x")

        self.lbl_users_title = tk.Label(
            self.stats_frame,
            text="KRİTİK VERİ GÖNDEREN CİHAZLAR",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="white"
        )
        self.lbl_users_title.pack()

        self.lbl_users_val = tk.Label(
            self.stats_frame,
            text=f"0 / {self.total_devices:,}",
            font=("Consolas", 24, "bold"),
            bg="#2c3e50",
            fg="#f1c40f"
        )
        self.lbl_users_val.pack(pady=5)

        self.lbl_load_title = tk.Label(
            self.stats_frame,
            text="ŞEBEKE YOĞUNLUĞU",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="white"
        )
        self.lbl_load_title.pack()

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("green.Horizontal.TProgressbar", foreground="green", background="green")
        self.style.configure("red.Horizontal.TProgressbar", foreground="red", background="red")
        self.style.configure("yellow.Horizontal.TProgressbar", foreground="#d4ac0d", background="#d4ac0d")
        self.style.configure("gray.Horizontal.TProgressbar", foreground="gray", background="gray")

        self.pb_load = ttk.Progressbar(
            self.stats_frame,
            style="green.Horizontal.TProgressbar",
            orient="horizontal",
            length=450,
            mode="determinate",
            maximum=100
        )
        self.pb_load.pack(pady=5)

        self.lbl_load_val = tk.Label(
            self.stats_frame,
            text="%35 (Stabil)",
            font=("Arial", 12, "bold"),
            bg="#2c3e50",
            fg="#2ecc71"
        )
        self.lbl_load_val.pack()

        # =========================
        # BUTONLAR
        # =========================
        self.btn_frame = tk.Frame(root, pady=15)
        self.btn_frame.pack(fill="x")

        self.start_btn = tk.Button(
            self.btn_frame,
            text="▶ SİMÜLASYONU BAŞLAT",
            command=self.start_simulation,
            bg="green",
            fg="white",
            font=("Arial", 10, "bold"),
            width=22
        )
        self.start_btn.pack(side="left", padx=12)

        self.stop_btn = tk.Button(
            self.btn_frame,
            text="⏸ DURDUR",
            command=self.stop_simulation,
            state="disabled",
            bg="orange",
            fg="white",
            font=("Arial", 10, "bold"),
            width=14
        )
        self.stop_btn.pack(side="left", padx=12)

        # Yeni buton
        self.reset_disaster_btn = tk.Button(
            self.btn_frame,
            text="🚨 DEPREM MODUNU KAPAT",
            command=self.reset_disaster_mode,
            bg="#c0392b",
            fg="white",
            font=("Arial", 10, "bold"),
            width=24
        )
        self.reset_disaster_btn.pack(side="left", padx=12)

        self.exit_btn = tk.Button(
            self.btn_frame,
            text="❌ ÇIKIŞ",
            command=self.close_app,
            bg="darkred",
            fg="white",
            font=("Arial", 10, "bold"),
            width=10
        )
        self.exit_btn.pack(side="right", padx=20)

        # =========================
        # TABLO
        # =========================
        self.list_frame = tk.Frame(root, pady=10)
        self.list_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            self.list_frame,
            columns=("Saat", "Kullanıcı", "Durum", "Kalite", "Süre"),
            show="headings",
            height=12
        )
        self.tree.heading("Saat", text="Zaman")
        self.tree.heading("Kullanıcı", text="Arama Tipi")
        self.tree.heading("Durum", text="Bağlantı Durumu")
        self.tree.heading("Kalite", text="Ses Kalitesi")
        self.tree.heading("Süre", text="Süre Limiti")

        self.tree.column("Saat", width=90, anchor="center")
        self.tree.column("Kullanıcı", width=170, anchor="center")
        self.tree.column("Durum", width=140, anchor="center")
        self.tree.column("Kalite", width=120, anchor="center")
        self.tree.column("Süre", width=120, anchor="center")

        self.tree.pack(fill="both", expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def start_simulation(self):
        if not self.is_running:
            self.is_running = True
            self.stop_event.clear()
            self.confirm_counter = 0
            self.disaster_locked = False
            self.disaster_start_time = None
            self.disaster_elapsed = 0

            self.start_btn.config(state="disabled", bg="gray")
            self.stop_btn.config(state="normal", bg="orange")

            self.thread = threading.Thread(target=self.loop_simulation, daemon=True)
            self.thread.start()

    def stop_simulation(self):
        self.is_running = False
        self.stop_event.set()
        self.confirm_counter = 0
        self.disaster_locked = False
        self.disaster_start_time = None
        self.disaster_elapsed = 0

        self.start_btn.config(state="normal", bg="green")
        self.stop_btn.config(state="disabled", bg="gray")

        self.status_frame.config(bg="gray")
        self.status_label.config(text="SİSTEM DURDURULDU", bg="gray")
        self.acc_label.config(text="Veri akışı kesildi.", bg="gray")
        self.cluster_label.config(
            text=f"Kritik veri gönderen cihaz: 0 / Eşik: {MIN_TRIGGER_DEVICES}",
            bg="gray"
        )
        self.confirm_label.config(
            text=f"Doğrulama: 0 / {CONFIRMATION_CYCLES}",
            bg="gray"
        )
        self.duration_label.config(
            text="Deprem Modu Süresi: 0 sn",
            bg="gray"
        )

    def reset_disaster_mode(self):
        self.disaster_locked = False
        self.confirm_counter = 0
        self.disaster_start_time = None
        self.disaster_elapsed = 0

    def close_app(self):
        self.is_running = False
        self.stop_event.set()
        self.root.destroy()

    def simulate_regional_devices(self, avg_acc):
        if avg_acc <= THRESHOLD:
            return 0

        delta = avg_acc - THRESHOLD

        if delta <= 0.20:
            return random.randint(80, 220)
        elif delta <= 0.40:
            return random.randint(180, 420)
        elif delta <= 0.70:
            return random.randint(350, 700)
        elif delta <= 1.00:
            return random.randint(650, 1050)
        elif delta <= 1.50:
            return random.randint(900, 1600)
        elif delta <= 2.50:
            return random.randint(1300, 2400)
        else:
            return random.randint(2000, 3800)

    def update_disaster_timer(self):
        if self.disaster_locked:
            if self.disaster_start_time is None:
                self.disaster_start_time = time.time()
            self.disaster_elapsed = int(time.time() - self.disaster_start_time)
        else:
            self.disaster_start_time = None
            self.disaster_elapsed = 0

    def update_ui(self, is_disaster, avg_acc, critical_devices, call_log=None):
        if not self.is_running:
            return

        self.critical_devices = critical_devices
        self.update_disaster_timer()

        if not self.sensor_ok:
            target_load = 20.0
        elif is_disaster:
            target_load = 96.0
        elif critical_devices > 0:
            target_load = 55.0
        else:
            target_load = 35.0

        self.network_load += (target_load - self.network_load) * 0.08
        self.network_load += random.uniform(-0.3, 0.3)
        self.network_load = max(0, min(100, self.network_load))

        if not self.sensor_ok:
            self.status_frame.config(bg="gray")
            self.status_label.config(text="⚠ SENSÖR BAĞLANTISI YOK", bg="gray")
            self.acc_label.config(text="Phyphox verisi alınamadı.", bg="gray")
            self.cluster_label.config(
                text=f"Kritik veri gönderen cihaz: 0 / Eşik: {MIN_TRIGGER_DEVICES}",
                bg="gray"
            )
            self.confirm_label.config(
                text=f"Doğrulama: 0 / {CONFIRMATION_CYCLES}",
                bg="gray"
            )
            self.duration_label.config(
                text="Deprem Modu Süresi: 0 sn",
                bg="gray"
            )

            self.pb_load.configure(style="gray.Horizontal.TProgressbar")
            self.lbl_load_val.config(text=f"%{int(self.network_load)} (Veri Yok)", fg="white")
            self.lbl_users_val.config(fg="white")

        elif is_disaster:
            self.status_frame.config(bg="red")
            self.status_label.config(text="🚨 DEPREM MODU AKTİF (KİLİTLENDİ) 🚨", bg="red")
            self.acc_label.config(text=f"Referans Sismik Veri: {avg_acc:.2f}", bg="red")
            self.cluster_label.config(
                text=f"Kritik veri gönderen cihaz: {critical_devices:,} / Eşik: {MIN_TRIGGER_DEVICES}",
                bg="red"
            )
            self.confirm_label.config(
                text=f"Doğrulama: {self.confirm_counter} / {CONFIRMATION_CYCLES}",
                bg="red"
            )
            self.duration_label.config(
                text=f"Deprem Modu Süresi: {self.disaster_elapsed} sn",
                bg="red"
            )

            self.pb_load.configure(style="red.Horizontal.TProgressbar")
            self.lbl_load_val.config(text=f"%{int(self.network_load)} (AŞIRI YÜK)", fg="#e74c3c")
            self.lbl_users_val.config(fg="#e74c3c")

        elif critical_devices > 0:
            self.status_frame.config(bg="#b8860b")
            self.status_label.config(text="⚠ ŞÜPHELİ SİSMİK HAREKET", bg="#b8860b")
            self.acc_label.config(text=f"Referans Sismik Veri: {avg_acc:.2f}", bg="#b8860b")
            self.cluster_label.config(
                text=f"Kritik veri gönderen cihaz: {critical_devices:,} / Eşik: {MIN_TRIGGER_DEVICES}",
                bg="#b8860b"
            )
            self.confirm_label.config(
                text=f"Doğrulama: {self.confirm_counter} / {CONFIRMATION_CYCLES}",
                bg="#b8860b"
            )
            self.duration_label.config(
                text="Deprem Modu Süresi: 0 sn",
                bg="#b8860b"
            )

            self.pb_load.configure(style="yellow.Horizontal.TProgressbar")
            self.lbl_load_val.config(text=f"%{int(self.network_load)} (Yükseliyor)", fg="#f1c40f")
            self.lbl_users_val.config(fg="#f1c40f")

        else:
            self.status_frame.config(bg="green")
            self.status_label.config(text="DURUM: NORMAL", bg="green")
            self.acc_label.config(text=f"Referans Sismik Veri: {avg_acc:.2f}", bg="green")
            self.cluster_label.config(
                text=f"Kritik veri gönderen cihaz: 0 / Eşik: {MIN_TRIGGER_DEVICES}",
                bg="green"
            )
            self.confirm_label.config(
                text=f"Doğrulama: 0 / {CONFIRMATION_CYCLES}",
                bg="green"
            )
            self.duration_label.config(
                text="Deprem Modu Süresi: 0 sn",
                bg="green"
            )

            self.pb_load.configure(style="green.Horizontal.TProgressbar")
            self.lbl_load_val.config(text=f"%{int(self.network_load)} (Stabil)", fg="#2ecc71")
            self.lbl_users_val.config(fg="#f1c40f")

        self.lbl_users_val.config(text=f"{critical_devices:,} / {self.total_devices:,}")
        self.pb_load["value"] = self.network_load

        if call_log:
            timestamp = time.strftime("%H:%M:%S")
            self.tree.insert(
                "",
                0,
                values=(
                    timestamp,
                    call_log["type"],
                    call_log["status"],
                    call_log["quality"],
                    call_log["limit"]
                )
            )

            if len(self.tree.get_children()) > 18:
                self.tree.delete(self.tree.get_children()[-1])

    def loop_simulation(self):
        while not self.stop_event.is_set():
            acc, sensor_ok = self.get_sensor_data()
            self.sensor_ok = sensor_ok

            if sensor_ok:
                self.history.append(acc)
                avg_acc = sum(self.history) / len(self.history)
                critical_devices = self.simulate_regional_devices(avg_acc)
            else:
                avg_acc = self.last_valid_acc
                critical_devices = 0
                self.confirm_counter = 0

            if not self.disaster_locked:
                if sensor_ok and avg_acc > THRESHOLD and critical_devices >= MIN_TRIGGER_DEVICES:
                    self.confirm_counter += 1
                else:
                    self.confirm_counter = 0

                if self.confirm_counter >= CONFIRMATION_CYCLES:
                    self.disaster_locked = True
                    if self.disaster_start_time is None:
                        self.disaster_start_time = time.time()

            is_disaster = self.disaster_locked

            caller = random.choice(CALLER_TYPES)

            if not sensor_ok:
                call_result = {
                    "type": caller["type"],
                    "status": "BEKLEMEDE",
                    "quality": "-",
                    "limit": "-"
                }
            elif is_disaster:
                if caller["priority"] == 1:
                    call_result = {
                        "type": caller["type"],
                        "status": "BAĞLANDI ✅",
                        "quality": "Yüksek (HD)",
                        "limit": "Sınırsız"
                    }
                elif caller["priority"] == 2:
                    call_result = {
                        "type": caller["type"],
                        "status": "BAĞLANDI ⚠️",
                        "quality": "Standart",
                        "limit": "Max 3dk"
                    }
                else:
                    call_result = {
                        "type": caller["type"],
                        "status": "KISITLI 📉",
                        "quality": "Düşük (AMR)",
                        "limit": "Max 60sn"
                    }
            elif critical_devices > 0:
                if caller["priority"] == 1:
                    call_result = {
                        "type": caller["type"],
                        "status": "BAĞLANDI",
                        "quality": "Yüksek (HD)",
                        "limit": "Sınırsız"
                    }
                elif caller["priority"] == 2:
                    call_result = {
                        "type": caller["type"],
                        "status": "BAĞLANDI",
                        "quality": "Standart",
                        "limit": "Max 5dk"
                    }
                else:
                    call_result = {
                        "type": caller["type"],
                        "status": "YOĞUNLUK VAR",
                        "quality": "Standart",
                        "limit": "Max 2dk"
                    }
            else:
                call_result = {
                    "type": caller["type"],
                    "status": "BAĞLANDI",
                    "quality": "Yüksek (HD)",
                    "limit": "Sınırsız"
                }

            self.root.after(0, self.update_ui, is_disaster, avg_acc, critical_devices, call_result)
            time.sleep(0.3)

    def get_sensor_data(self):
        try:
            response = requests.get(PHYPHOX_URL, timeout=2.0)
            response.raise_for_status()

            data = response.json()

            ax_buffer = data["buffer"]["accX"]["buffer"]
            ay_buffer = data["buffer"]["accY"]["buffer"]
            az_buffer = data["buffer"]["accZ"]["buffer"]

            if not ax_buffer or not ay_buffer or not az_buffer:
                self.failed_reads += 1
                if self.failed_reads < self.max_failed_reads:
                    return self.last_valid_acc, True
                return self.last_valid_acc, False

            ax = ax_buffer[0]
            ay = ay_buffer[0]
            az = az_buffer[0]

            magnitude = (ax ** 2 + ay ** 2 + az ** 2) ** 0.5

            self.last_valid_acc = magnitude
            self.failed_reads = 0

            return magnitude, True

        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
            self.failed_reads += 1

            if self.failed_reads < self.max_failed_reads:
                return self.last_valid_acc, True

            return self.last_valid_acc, False


if __name__ == "__main__":
    root = tk.Tk()
    app = OperatorApp(root)
    root.mainloop()
