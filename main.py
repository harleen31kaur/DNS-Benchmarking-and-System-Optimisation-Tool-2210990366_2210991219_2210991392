import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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
        self.root.title("DNS Benchmarking and System Optimization Tool")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 650)

        # Detect OS for platform-specific adjustments
        self.os_name = platform.system()

        # Initialize ttk styles for cross-platform consistency
        self.setup_ttk_styles()

        self.dns = DNS_SERVERS.copy()
        self.results = []
        self.live = False
        self.analysis_running = False
        self.theme_mode = "dark"

        self.build_ui()
        self.build_graph()
        self.apply_theme()

    # ================= TTK STYLES SETUP ================= #
    def setup_ttk_styles(self):
        """Setup ttk styles for cross-platform consistency"""
        self.style = ttk.Style()

        # Use 'clam' theme for better cross-platform consistency
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            # Fallback to default theme if clam is not available
            pass

        # Configure base styles
        self.style.configure('TFrame', background='#ffffff')
        self.style.configure('Card.TFrame', background='#f3f4f6')

        # Button styles
        self.style.configure('TButton',
                           font=('Segoe UI', 9),
                           padding=5)

        # Label styles
        self.style.configure('TLabel',
                           font=('Segoe UI', 9),
                           background='#ffffff')

        self.style.configure('Title.TLabel',
                           font=('Segoe UI', 11, 'bold'),
                           background='#f3f4f6')

        self.style.configure('Status.TLabel',
                           font=('Segoe UI', 9),
                           background='#f3f4f6')

        # Treeview styles
        self.style.configure('Treeview',
                           font=('Segoe UI', 9),
                           rowheight=25)

        self.style.configure('Treeview.Heading',
                           font=('Segoe UI', 10, 'bold'))

    # ================= UI ================= #
    def build_ui(self):

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # TOP BAR
        self.topbar = ttk.Frame(self.root, style='Card.TFrame')
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.title = ttk.Label(self.topbar, text="DNS ENTERPRISE ANALYZER", style='Title.TLabel')
        self.title.pack(side=tk.LEFT, padx=15)

        self.status = ttk.Label(self.topbar, text="IDLE", style='Status.TLabel')
        self.status.pack(side=tk.RIGHT, padx=15)

        self.theme_btn = ttk.Button(self.topbar, text="Theme", command=self.toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=5)

        # SIDEBAR
        self.sidebar = ttk.Frame(self.root, width=260, style='Card.TFrame')
        self.sidebar.grid(row=1, column=0, sticky="ns")
        self.sidebar.pack_propagate(False)

        ttk.Label(self.sidebar, text="CONTROL PANEL", style='Title.TLabel').pack(pady=10)

        ttk.Button(self.sidebar, text="Analyze", command=self.run_analysis).pack(fill=tk.X, padx=10, pady=5)
        self.live_btn = ttk.Button(self.sidebar, text="Live Mode", command=self.toggle_live)
        self.live_btn.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(self.sidebar, text="Apply Fastest DNS", command=self.apply_fastest_dns).pack(fill=tk.X, padx=10, pady=5)

        # ── SINGLE EXPORT BUTTON ── #
        ttk.Button(self.sidebar, text="Export", command=self.export_dialog).pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(self.sidebar, text="+ Add Custom DNS", command=self.add_dns).pack(fill=tk.X, padx=10, pady=10)

        self.progress = ttk.Progressbar(self.sidebar)
        self.progress.pack(fill=tk.X, padx=10, pady=10)

        # MAIN AREA
        self.main = ttk.Frame(self.root, style='TFrame')
        self.main.grid(row=1, column=1, sticky="nsew")

        self.main.grid_rowconfigure(2, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.fastest_label = ttk.Label(self.main, text="Fastest: --", style='TLabel')
        self.fastest_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        # TABLE
        self.table_frame = ttk.Frame(self.main, style='TFrame')
        self.table_frame.grid(row=1, column=0, sticky="nsew")

        self.tree = ttk.Treeview(self.table_frame, columns=("dns", "ip", "lat"), show="headings")

        self.tree.heading("dns", text="DNS Provider")
        self.tree.heading("ip", text="IP Address")
        self.tree.heading("lat", text="Latency (ms)")

        self.tree.column("dns", anchor="center", width=200)
        self.tree.column("ip", anchor="center", width=200)
        self.tree.column("lat", anchor="center", width=150)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Add right-click context menu for deleting DNS entries
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Delete DNS", command=self.delete_selected_dns)

        # Bind right-click to show context menu
        self.tree.bind("<Button-3>", self.show_context_menu)  # macOS right-click
        self.tree.bind("<Button-2>", self.show_context_menu)  # Alternative for some systems

        # GRAPH
        self.graph_frame = ttk.Frame(self.main, style='TFrame')
        self.graph_frame.grid(row=2, column=0, sticky="nsew")

        # LOGS
        self.log = tk.Text(self.root, height=8)
        self.log.grid(row=2, column=0, columnspan=2, sticky="ew")

    # ================= CONTEXT MENU ================= #
    def show_context_menu(self, event):
        """Show right-click context menu for DNS deletion"""
        # Select the item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def delete_selected_dns(self):
        """Delete the selected DNS entry"""
        selection = self.tree.selection()
        if not selection:
            return

        # Get the DNS name from the selected row
        item = selection[0]
        values = self.tree.item(item, 'values')
        dns_name = values[0]  # First column is DNS name

        # Prevent deleting the last DNS server
        if len(self.dns) <= 1:
            messagebox.showwarning("Cannot Delete", "At least one DNS server must remain for analysis.")
            return

        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Delete DNS server '{dns_name}'?"):
            # Remove from DNS dictionary
            if dns_name in self.dns:
                del self.dns[dns_name]
                self.add_log(f"DNS Deleted: {dns_name}")

                # Clear results immediately
                self.results = []
                self.tree.delete(*self.tree.get_children())
                self.fastest_label.config(text="Fastest: --")
                self.status.config(text="IDLE")
                self.progress["value"] = 0

                if self.live:
                    self.add_log("Live mode active — refresh will occur on next cycle")
                else:
                    if self.dns:
                        self.run_analysis()
                    else:
                        self.add_log("No DNS servers remaining")

    # ================= UI CONTINUATION ================= #
    # GRAPH
    def build_graph(self):
        self.fig = plt.Figure(figsize=(6, 3))
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ================= ANALYZE ================= #
    def run_analysis(self):
        if self.analysis_running:
            return
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        if self.analysis_running:
            return
        self.analysis_running = True
        try:
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
        finally:
            self.analysis_running = False

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
        """Add custom DNS with ttk-based dialog for cross-platform consistency"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Custom DNS")
        dialog.geometry("350x230")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.root)

        # Apply theme colors to dialog
        if self.theme_mode == "dark":
            dialog.configure(bg="#0f172a")
        else:
            dialog.configure(bg="#f3f4f6")

        MAX_NAME_LEN = 30

        # Use ttk widgets for consistency
        ttk.Label(dialog, text="DNS Name:", style='TLabel').pack(pady=(14, 0), padx=14, anchor="w")
        name_entry = ttk.Entry(dialog, font=("Segoe UI", 10))
        name_entry.pack(fill=tk.X, padx=14, pady=(4, 0))
        name_entry.focus()

        name_count_label = ttk.Label(dialog, text=f"0 / {MAX_NAME_LEN}", style='TLabel')
        name_count_label.pack(padx=14, anchor="e")

        def on_name_change(*args):
            current = len(name_entry.get())
            if current > MAX_NAME_LEN:
                name_entry.delete(MAX_NAME_LEN, tk.END)
                current = MAX_NAME_LEN
            name_count_label.config(text=f"{current} / {MAX_NAME_LEN}")

        name_entry.bind("<KeyRelease>", on_name_change)

        ttk.Label(dialog, text="DNS Address (IP):", style='TLabel').pack(pady=(8, 0), padx=14, anchor="w")
        addr_entry = ttk.Entry(dialog, font=("Segoe UI", 10))
        addr_entry.pack(fill=tk.X, padx=14, pady=4)

        btn_frame = ttk.Frame(dialog, style='TFrame')
        btn_frame.pack(pady=16)

        def validate_ip(ip):
            """Validate IPv4 address format: four octets, each 0-255"""
            parts = ip.split(".")
            if len(parts) != 4:
                return False
            for part in parts:
                if not part.isdigit():
                    return False
                if not (0 <= int(part) <= 255):
                    return False
            return True

        def save_dns():
            name = name_entry.get().strip()
            addr = addr_entry.get().strip()

            # ── VALIDATION ── #
            if not name:
                messagebox.showerror("Validation Error", "DNS Name cannot be empty.", parent=dialog)
                name_entry.focus()
                return

            if len(name) < 2:
                messagebox.showerror("Validation Error", "DNS Name must be at least 2 characters long.", parent=dialog)
                name_entry.focus()
                return

            if name in self.dns:
                messagebox.showerror("Validation Error", f"A DNS entry named '{name}' already exists.", parent=dialog)
                name_entry.focus()
                return

            if not addr:
                messagebox.showerror("Validation Error", "DNS IP Address cannot be empty.", parent=dialog)
                addr_entry.focus()
                return

            if not validate_ip(addr):
                messagebox.showerror("Validation Error", "Invalid IP Address.\nPlease enter a valid IPv4 address (e.g. 8.8.8.8).", parent=dialog)
                addr_entry.focus()
                return

            if addr in self.dns.values():
                messagebox.showerror("Validation Error", f"The IP address '{addr}' is already in the DNS list.", parent=dialog)
                addr_entry.focus()
                return

            # ── SAVE ── #
            self.dns[name] = addr
            self.add_log(f"DNS Added: {name} → {addr}")
            dialog.destroy()
            self.run_analysis()

        # Use ttk buttons for consistency
        ttk.Button(btn_frame, text="OK", command=save_dns).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=6)

    # ================= LIVE ================= #
    def toggle_live(self):
        self.live = not self.live
        if self.live:
            self.live_btn.config(text="⏹ Live Mode (ON)")
            self.add_log("Live Mode: ON")
            threading.Thread(target=self._live_loop, daemon=True).start()
        else:
            self.live_btn.config(text="Live Mode")
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
        """Export dialog using ttk widgets for cross-platform consistency"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Export As")
        dialog.geometry("280x210")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.root)

        # Apply theme colors
        if self.theme_mode == "dark":
            dialog.configure(bg="#0f172a")
        else:
            dialog.configure(bg="#f3f4f6")

        ttk.Label(dialog, text="Choose Export Format", style='Title.TLabel').pack(pady=(18, 12))

        def do_export(fmt):
            dialog.destroy()
            if fmt == "pdf":
                self.export_pdf()
            elif fmt == "csv":
                self.export_csv()
            elif fmt == "excel":
                self.export_excel()

        # Use ttk buttons for consistency
        ttk.Button(dialog, text="📄  PDF", command=lambda: do_export("pdf")).pack(pady=5)
        ttk.Button(dialog, text="📊  CSV", command=lambda: do_export("csv")).pack(pady=5)
        ttk.Button(dialog, text="📗  Excel (.xlsx)", command=lambda: do_export("excel")).pack(pady=5)

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
        """Apply theme using ttk styles for cross-platform consistency"""

        if self.theme_mode == "dark":
            # Dark theme colors
            bg = "#0a0f1a"
            card = "#0f172a"
            fg = "white"
            accent = "#38bdf8"
            button_bg = "#374151"
            button_fg = "white"
            tree_bg = "#1f2937"
            tree_fg = "white"
            tree_heading_bg = "#111827"
            tree_heading_fg = "white"
        else:
            # Light theme colors
            bg = "#ffffff"
            card = "#f3f4f6"
            fg = "black"
            accent = "#3b82f6"
            button_bg = "#f3f4f6"
            button_fg = "black"
            tree_bg = "#ffffff"
            tree_fg = "black"
            tree_heading_bg = "#f9fafb"
            tree_heading_fg = "black"

        # Configure ttk styles
        self.style.configure('TFrame', background=bg)
        self.style.configure('Card.TFrame', background=card)

        self.style.configure('TButton',
                           background=button_bg,
                           foreground=button_fg,
                           font=('Segoe UI', 9))

        self.style.configure('TLabel',
                           background=bg,
                           foreground=fg,
                           font=('Segoe UI', 9))

        self.style.configure('Title.TLabel',
                           background=card,
                           foreground=fg,
                           font=('Segoe UI', 11, 'bold'))

        self.style.configure('Status.TLabel',
                           background=card,
                           foreground=fg,
                           font=('Segoe UI', 9))

        # Treeview styling
        self.style.configure('Treeview',
                           background=tree_bg,
                           foreground=tree_fg,
                           fieldbackground=tree_bg,
                           font=('Segoe UI', 9),
                           rowheight=25)

        self.style.configure('Treeview.Heading',
                           background=tree_heading_bg,
                           foreground=tree_heading_fg,
                           font=('Segoe UI', 10, 'bold'))

        # Map for interactive states
        self.style.map('TButton',
                      background=[('active', accent),
                                ('pressed', accent)])

        self.style.map('Treeview',
                      background=[('selected', accent)],
                      foreground=[('selected', 'white')])

        # Update root window background (tk widget)
        self.root.configure(bg=bg)

        # Update log widget (tk widget, not ttk)
        if hasattr(self, 'log'):
            self.log.configure(bg=card, fg=fg, insertbackground=fg)

        # Update graph background
        self.draw_graph()

        # Don't log theme changes during initialization

    # ================= THEME TOGGLE ================= #
    def toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.apply_theme()
        self.add_log(f"Theme switched → {self.theme_mode}")


# ================= RUN ================= #
root = tk.Tk()
app = DNSApp(root)
root.mainloop()