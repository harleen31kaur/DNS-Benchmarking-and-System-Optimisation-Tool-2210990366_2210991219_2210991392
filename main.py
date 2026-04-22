import tkinter as tk
from tkinter import ttk, filedialog
import socket
import threading
import time
import csv
import platform
import subprocess
import sys
import ctypes
from openpyxl import Workbook
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4


# ================= DNS ================= #
DNS_SERVERS = {
    "Google": "8.8.8.8",
    "Cloudflare": "1.1.1.1",
    "OpenDNS": "208.67.222.222",
    "Quad9": "9.9.9.9"
}


# ================= PING ================= #
def ping(ip):
    try:
        start = time.time()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((ip, 53))
        return round((time.time() - start) * 1000, 2)
    except:
        return None


# ================= APP ================= #
class DNSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DNS Enterprise Analyzer")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 650)

        self.dns = DNS_SERVERS.copy()
        self.results = []
        self.live = False
        self.theme_mode = "dark"

        self.build_ui()
        self.build_graph()
        self.apply_theme()

    # ================= UI ================= #
    def build_ui(self):

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # TOP BAR
        self.topbar = tk.Frame(self.root)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.title = tk.Label(self.topbar, text="DNS ENTERPRISE ANALYZER", font=("Segoe UI", 11, "bold"))
        self.title.pack(side=tk.LEFT, padx=15)

        self.status = tk.Label(self.topbar, text="IDLE")
        self.status.pack(side=tk.RIGHT, padx=15)

        tk.Button(self.topbar, text="Theme", command=self.toggle_theme).pack(side=tk.RIGHT, padx=5)

        # SIDEBAR
        self.sidebar = tk.Frame(self.root, width=260)
        self.sidebar.grid(row=1, column=0, sticky="ns")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="CONTROL PANEL", font=("Segoe UI", 10, "bold")).pack(pady=10)

        tk.Button(self.sidebar, text="Analyze", command=self.run_analysis).pack(fill=tk.X, padx=10, pady=5)
        self.live_btn = tk.Button(self.sidebar, text="Live Mode", command=self.toggle_live)
        self.live_btn.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(self.sidebar, text="Apply Fastest DNS", command=self.apply_fastest_dns).pack(fill=tk.X, padx=10, pady=5)

        # ── SINGLE EXPORT BUTTON ── #
        tk.Button(self.sidebar, text="Export", command=self.export_dialog).pack(fill=tk.X, padx=10, pady=5)

        tk.Button(self.sidebar, text="+ Add Custom DNS", command=self.add_dns).pack(fill=tk.X, padx=10, pady=10)

        self.progress = ttk.Progressbar(self.sidebar)
        self.progress.pack(fill=tk.X, padx=10, pady=10)

        # MAIN AREA
        self.main = tk.Frame(self.root)
        self.main.grid(row=1, column=1, sticky="nsew")

        self.main.grid_rowconfigure(2, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.fastest_label = tk.Label(self.main, text="Fastest: --")
        self.fastest_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        # TABLE
        self.table_frame = tk.Frame(self.main)
        self.table_frame.grid(row=1, column=0, sticky="nsew")

        self.tree = ttk.Treeview(self.table_frame, columns=("dns", "ip", "lat"), show="headings")

        self.tree.heading("dns", text="DNS Provider")
        self.tree.heading("ip", text="IP Address")
        self.tree.heading("lat", text="Latency (ms)")

        self.tree.column("dns", anchor="center", width=200)
        self.tree.column("ip", anchor="center", width=200)
        self.tree.column("lat", anchor="center", width=150)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # GRAPH
        self.graph_frame = tk.Frame(self.main)
        self.graph_frame.grid(row=2, column=0, sticky="nsew")

        # LOGS
        self.log = tk.Text(self.root, height=8)
        self.log.grid(row=2, column=0, columnspan=2, sticky="ew")

    # ================= GRAPH ================= #
    def build_graph(self):
        self.fig = plt.Figure(figsize=(6, 3))
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ================= ANALYZE ================= #
    def run_analysis(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self.tree.delete(*self.tree.get_children())
        self.results = []

        best = None
        best_val = 9999

        self.progress["maximum"] = len(self.dns)

        for i, (name, ip) in enumerate(self.dns.items()):
            lat = ping(ip) or 999
            self.results.append((name, ip, lat))

            self.add_log(f"{name} → {lat} ms")

            if lat < best_val:
                best_val = lat
                best = (name, ip, lat)

            self.progress["value"] = i + 1

        self.update_ui(best)
        self.draw_graph()

    # ================= UI ================= #
    def update_ui(self, best):
        for n, ip, lat in self.results:
            self.tree.insert("", tk.END, values=(n, ip, lat))

        if best:
            self.fastest_label.config(text=f"Fastest: {best[0]} ({best[2]} ms)")
            self.status.config(text="RUNNING")

    # ================= LOG ================= #
    def add_log(self, text):
        self.log.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {text}\n")
        self.log.see(tk.END)

    # ================= GRAPH (FIXED THEME SAFE) ================= #
    def draw_graph(self):
        self.ax.clear()

        if not self.results:
            self.canvas.draw()
            return

        names = [n for n, _, _ in self.results]
        vals = [v for _, _, v in self.results]

        # BAR COLOR ALWAYS VISIBLE
        self.ax.bar(names, vals, color="#38bdf8")

        # THEME COLORS
        if self.theme_mode == "dark":
            text_color = "white"
            bg = "#0a0f1a"
            grid = "#334155"
        else:
            text_color = "black"
            bg = "#ffffff"
            grid = "#e5e7eb"

        # GRAPH BACKGROUND FIX (IMPORTANT)
        self.fig.patch.set_facecolor(bg)
        self.ax.set_facecolor(bg)

        # TEXT
        self.ax.set_title("DNS Latency Comparison", color=text_color)
        self.ax.set_xlabel("DNS Servers", color=text_color)
        self.ax.set_ylabel("Latency (ms)", color=text_color)

        
        self.ax.tick_params(axis='x', colors=text_color, pad=-3)
        self.ax.tick_params(axis='y', colors=text_color)

        # GRID
        self.ax.grid(True, linestyle="--", color=grid, alpha=0.5)

        # BORDER
        for spine in self.ax.spines.values():
            spine.set_color(grid)

        self.canvas.draw_idle()

    # ================= ADD DNS (FIXED BUTTON VISIBILITY) ================= #
    def add_dns(self):
        # Determine colors based on current theme
        if self.theme_mode == "dark":
            dlg_bg  = "#0f172a"
            dlg_fg  = "white"
            entry_bg = "#1e293b"
            entry_fg = "white"
        else:
            dlg_bg  = "#f3f4f6"
            dlg_fg  = "black"
            entry_bg = "white"
            entry_fg = "black"

        dialog = tk.Toplevel(self.root)
        dialog.title("Add Custom DNS")
        dialog.geometry("350x210")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.root)
        dialog.configure(bg=dlg_bg)

        tk.Label(dialog, text="DNS Name:", font=("Segoe UI", 10),
                 bg=dlg_bg, fg=dlg_fg).pack(pady=(14, 0), padx=14, anchor="w")
        name_entry = tk.Entry(dialog, font=("Segoe UI", 10),
                              bg=entry_bg, fg=entry_fg, insertbackground=dlg_fg,
                              relief="solid", bd=1)
        name_entry.pack(fill=tk.X, padx=14, pady=4)
        name_entry.focus()

        tk.Label(dialog, text="DNS Address (IP):", font=("Segoe UI", 10),
                 bg=dlg_bg, fg=dlg_fg).pack(pady=(8, 0), padx=14, anchor="w")
        addr_entry = tk.Entry(dialog, font=("Segoe UI", 10),
                              bg=entry_bg, fg=entry_fg, insertbackground=dlg_fg,
                              relief="solid", bd=1)
        addr_entry.pack(fill=tk.X, padx=14, pady=4)

        btn_frame = tk.Frame(dialog, bg=dlg_bg)
        btn_frame.pack(pady=16)

        def save_dns():
            name = name_entry.get().strip()
            addr = addr_entry.get().strip()
            if not name or not addr:
                self.add_log("Error: Both name and address required")
                return
            self.dns[name] = addr
            self.add_log(f"DNS Added: {name} → {addr}")
            dialog.destroy()
            self.run_analysis()

        tk.Button(btn_frame, text="OK", command=save_dns, width=10,
                  bg="#10b981", fg="white", activebackground="#059669",
                  activeforeground="white", relief="flat").pack(side=tk.LEFT, padx=6)

        tk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=10,
                  bg="#ef4444", fg="white", activebackground="#dc2626",
                  activeforeground="white", relief="flat").pack(side=tk.LEFT, padx=6)

    # ================= LIVE ================= #
    def toggle_live(self):
        self.live = not self.live
        if self.live:
            self.live_btn.config(text="⏹ Live Mode (ON)", relief="sunken")
            self.add_log("Live Mode: ON")
            threading.Thread(target=self._live_loop, daemon=True).start()
        else:
            self.live_btn.config(text="Live Mode", relief="raised")
            self.add_log("Live Mode: OFF")

    def _live_loop(self):
        while self.live:
            self._run()
            time.sleep(3)

    # ================= APPLY DNS ================= #
    def apply_fastest_dns(self):
        if not self.results:
            self.add_log("No DNS data")
            return

        best = min(self.results, key=lambda x: x[2])
        self.change_dns(best[1])


##### func to change system DNS (requires admin/sudo access) - works on Windows, macOS, and Linux (with fallback message) #####
    def change_dns(self, dns_ip):
        os_name = platform.system()
        
        if os_name == "Windows":
            if not ctypes.windll.shell32.IsUserAnAdmin():
                self.add_log("Requesting admin access...")
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                self.root.destroy()
                return

            subprocess.call(f'netsh interface ip set dns "Wi-Fi" static {dns_ip}', shell=True)
            self.add_log(f"DNS changed → {dns_ip}")

        elif os_name == "Darwin":  # macOS
            try:
                result = subprocess.run(
                    "networksetup -listallnetworkservices | head -2 | tail -1",
                    shell=True, capture_output=True, text=True
                )
                interface = result.stdout.strip()
                
                if interface:
                    subprocess.run(
                        f"sudo networksetup -setdnsservers '{interface}' {dns_ip}",
                        shell=True, capture_output=True
                    )
                    self.add_log(f"DNS changed → {dns_ip} (macOS)")
                else:
                    self.add_log("Error: Could not detect network interface")
            except Exception as e:
                self.add_log(f"Error changing DNS on macOS: {str(e)}")

        elif os_name == "Linux":
            try:
                subprocess.run(
                    f"sudo resolvectl default-route --set {dns_ip}",
                    shell=True, capture_output=True
                )
                self.add_log(f"DNS changed → {dns_ip} (Linux)")
            except Exception as e:
                self.add_log(f"Linux: sudo access required to change DNS. Manual config needed.")
        
        else:
            self.add_log(f"Unsupported OS: {os_name}")

    # ================= EXPORT DIALOG ================= #
    def export_dialog(self):
        if self.theme_mode == "dark":
            dlg_bg = "#0f172a"
            dlg_fg = "white"
            btn_bg = "#1e293b"
            btn_fg = "white"
            btn_active = "#334155"
        else:
            dlg_bg = "#f3f4f6"
            dlg_fg = "black"
            btn_bg = "#e5e7eb"
            btn_fg = "black"
            btn_active = "#d1d5db"

        dialog = tk.Toplevel(self.root)
        dialog.title("Export As")
        dialog.geometry("280x210")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.root)
        dialog.configure(bg=dlg_bg)

        tk.Label(dialog, text="Choose Export Format", font=("Segoe UI", 11, "bold"),
                 bg=dlg_bg, fg=dlg_fg).pack(pady=(18, 12))

        btn_cfg = dict(width=18, font=("Segoe UI", 10), relief="flat",
                       bg=btn_bg, fg=btn_fg, activebackground=btn_active,
                       activeforeground=btn_fg, cursor="hand2")

        def do_export(fmt):
            dialog.destroy()
            if fmt == "pdf":
                self.export_pdf()
            elif fmt == "csv":
                self.export_csv()
            elif fmt == "excel":
                self.export_excel()

        tk.Button(dialog, text="📄  PDF", command=lambda: do_export("pdf"),   **btn_cfg).pack(pady=5)
        tk.Button(dialog, text="📊  CSV", command=lambda: do_export("csv"),   **btn_cfg).pack(pady=5)
        tk.Button(dialog, text="📗  Excel (.xlsx)", command=lambda: do_export("excel"), **btn_cfg).pack(pady=5)

    # ================= EXPORT ================= #
    def export_pdf(self):
        file = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not file:
            return

        pdf = pdf_canvas.Canvas(file, pagesize=A4)
        y = 800

        for n, ip, lat in self.results:
            pdf.drawString(50, y, f"{n} | {ip} | {lat}")
            y -= 20

        pdf.save()

    def export_csv(self):
        file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not file:
            return

        with open(file, "w", newline="") as f:
            csv.writer(f).writerows(self.results)

    def export_excel(self):
        file = filedialog.asksaveasfilename(defaultextension=".xlsx")
        if not file:
            return

        wb = Workbook()
        ws = wb.active
        ws.append(["DNS", "IP", "Latency"])

        for r in self.results:
            ws.append(r)

        wb.save(file)

    # ================= THEME ================= #
    def apply_theme(self):

        if self.theme_mode == "dark":
            bg = "#0a0f1a"
            card = "#0f172a"
            fg = "white"
        else:
            bg = "#ffffff"
            card = "#f3f4f6"
            fg = "black"

        self.root.configure(bg=bg)
        self.main.configure(bg=bg)
        self.sidebar.configure(bg=card)
        self.topbar.configure(bg=card)
        self.table_frame.configure(bg=bg)
        self.graph_frame.configure(bg=bg)
        self.log.configure(bg=card, fg=fg)

        self.title.configure(bg=card, fg=fg)
        self.status.configure(bg=card, fg=fg)
        self.fastest_label.configure(bg=bg, fg=fg)

        # TABLE THEME FIX
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
            background=card,
            fieldbackground=card,
            foreground=fg,
            rowheight=28
        )

        style.configure("Treeview.Heading",
            background=bg,
            foreground=fg,
            font=("Segoe UI", 10, "bold")
        )

        style.map("Treeview",
            background=[("selected", "#38bdf8")],
            foreground=[("selected", "black")]
        )

    # ================= THEME TOGGLE ================= #
    def toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.apply_theme()
        self.add_log(f"Theme switched → {self.theme_mode}")


# ================= RUN ================= #
root = tk.Tk()
app = DNSApp(root)
root.mainloop()