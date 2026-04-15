import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import socket
import threading
import time
import platform
import subprocess
import ctypes
import os
import sys  
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas
import matplotlib
matplotlib.use("TkAgg")

DEFAULT_DNS_SERVERS = {
    'Google': '8.8.8.8',
    'Cloudflare': '1.1.1.1',
    'OpenDNS': '208.67.222.222',
    'Quad9': '9.9.9.9'
}

THEMES = {
    'dark': {
        'bg': '#1e1e1e',
        'fg': '#ffffff',
        'accent': "#6fff00",
        'text_bg': '#111111',
        'text_fg': 'lime',
        'tree_bg': '#2e2e2e',
        'tree_fg': 'white',
        'tree_field': '#2e2e2e',
        'tree_heading': '#333333',
        'button_bg': '#008080',
        'export_bg': '#444444',
        'figure_facecolor': '#1e1e1e',
        'axis_color': 'white'
    },
    'light': {
        'bg': '#f0f0f0',
        'fg': '#000000',
        'accent': '#0066cc',
        'text_bg': '#ffffff',
        'text_fg': 'black',
        'tree_bg': '#ffffff',
        'tree_fg': 'black',
        'tree_field': '#ffffff',
        'tree_heading': '#e0e0e0',
        'button_bg': '#4CAF50',
        'export_bg': '#607d8b',
        'figure_facecolor': '#f5f5f5',
        'axis_color': 'black'
    }
}

def measure_latency(dns_ip, timeout=2):
    try:
        start = time.time()
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((dns_ip, 53))
        return round((time.time() - start) * 1000, 2)
    except:
        return None

class DNSAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DNS Analyzer Tool")
        self.root.geometry("900x680")
        
        self.current_theme = 'dark'
        self.dns_servers = DEFAULT_DNS_SERVERS.copy()
        self.results = []
        self.fastest_dns = None
        
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.header_frame = tk.Frame(self.root)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.content_frame = tk.Frame(self.root)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        
        # HEADER
        self.title_label = tk.Label(
            self.header_frame,
            text="DNS Analyzer Tool",
            font=("Segoe UI", 22, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        self.theme_button = tk.Button(
            self.header_frame,
            text="☀️",
            command=self.toggle_theme,
            font=("Segoe UI", 12),
            relief="flat"
        )
        self.theme_button.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # ENTRY
        self.entry_frame = tk.Frame(self.content_frame)
        self.entry_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(self.entry_frame, text="Add Custom DNS IP:").grid(row=0, column=0, padx=5)
        self.custom_entry = tk.Entry(self.entry_frame)
        self.custom_entry.grid(row=0, column=1, sticky="ew", padx=5)
        tk.Button(self.entry_frame, text="➕ Add", command=self.add_custom_dns).grid(row=0, column=2, padx=5)
        
        # CONTROL
        self.control_frame = tk.Frame(self.content_frame)
        self.control_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.button_frame = tk.Frame(self.control_frame)
        self.button_frame.pack(fill=tk.X)
        
        self.analyze_button = tk.Button(
            self.button_frame,
            text="🚀 Analyze DNS Servers",
            command=self.start_analysis,
            relief="flat",
            padx=10
        )
        self.analyze_button.pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(self.button_frame, mode='determinate')
        self.progress.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)
        
        # TABLE
        self.tree = ttk.Treeview(self.control_frame, columns=("IP", "Latency"), show='headings', height=6)
        self.tree.heading("IP", text="DNS IP")
        self.tree.heading("Latency", text="Latency (ms)")
        self.tree.column("IP", anchor="center")
        self.tree.column("Latency", anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # GRAPH
        self.figure = plt.Figure(figsize=(6, 3), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.control_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)
        
        # STATUS
        self.status_text = tk.Text(self.control_frame, height=6, font=("Consolas", 10))
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # EXPORT
        self.export_button = tk.Button(
            self.content_frame,
            text="📄 Export Summary as PDF",
            command=self.export_to_pdf,
            relief="flat",
            padx=10
        )
        self.export_button.pack(pady=10)

    def apply_theme(self):
        theme = THEMES[self.current_theme]
        
        self.root.configure(bg=theme['bg'])
        self.header_frame.configure(bg=theme['bg'])
        self.content_frame.configure(bg=theme['bg'])
        self.entry_frame.configure(bg=theme['bg'])
        self.control_frame.configure(bg=theme['bg'])
        self.button_frame.configure(bg=theme['bg'])
        
        self.title_label.configure(bg=theme['bg'], fg=theme['accent'])
        self.theme_button.configure(bg=theme['bg'], fg=theme['fg'])
        
        for child in self.entry_frame.winfo_children():
            if isinstance(child, tk.Label):
                child.configure(bg=theme['bg'], fg=theme['fg'])
            elif isinstance(child, tk.Entry):
                child.configure(bg='white', fg='black')
        
        self.analyze_button.configure(bg=theme['button_bg'], fg='white')
        self.export_button.configure(bg=theme['export_bg'], fg='white')
        
        self.style.configure("Treeview",
                            background=theme['tree_bg'],
                            foreground=theme['tree_fg'],
                            fieldbackground=theme['tree_field'])
        
        self.status_text.configure(bg=theme['text_bg'], fg=theme['text_fg'])
        
        self.figure.set_facecolor('#1e1e1e')
        self.ax.set_facecolor('#1e1e1e')

    def toggle_theme(self):
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.theme_button.config(text="🌙" if self.current_theme == 'dark' else "☀️")
        self.apply_theme()

    def redraw_graph(self):
        if not self.results:
            return
            
        min_latency = min([r[2] for r in self.results if isinstance(r[2], float)], default=0)
        
        self.ax.clear()
        names = [f"{name}\n{ip}" for name, ip, _ in self.results]
        latencies = [lat if isinstance(lat, float) else 0 for _, _, lat in self.results]

        colors = ['#00ff88' if lat == min_latency else '#00c853' for lat in latencies]

        self.ax.barh(names, latencies, color=colors)

        self.ax.set_title("DNS Server Latency", color='white', pad=10)
        self.ax.set_xlabel("Latency (ms)", color='white', labelpad=10)

        self.ax.tick_params(colors='white')

        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#888')
        self.ax.spines['left'].set_color('#888')

        self.ax.grid(True, linestyle="--", alpha=0.2, color='white')

        self.figure.tight_layout()
        self.figure.subplots_adjust(bottom=0.2)

        self.canvas.draw()

    def log_status(self, msg):
        self.status_text.insert(tk.END, msg + "\n")
        self.status_text.see(tk.END)

    def add_custom_dns(self):
        ip = self.custom_entry.get().strip()
        if ip:
            self.dns_servers[f"Custom-{ip}"] = ip
            self.custom_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Added {ip}")
        else:
            messagebox.showwarning("Error", "Enter valid IP")

    def start_analysis(self):
        self.analyze_button.config(state="disabled")
        threading.Thread(target=self.analyze_dns_servers).start()

    def analyze_dns_servers(self):
        self.tree.delete(*self.tree.get_children())
        self.results = []
        self.status_text.delete("1.0", tk.END)

        self.progress["maximum"] = len(self.dns_servers)
        self.progress["value"] = 0

        best = None
        min_latency = float('inf')

        for i, (name, ip) in enumerate(self.dns_servers.items(), 1):
            self.log_status(f"Testing {name} ({ip})...")
            latency = measure_latency(ip)

            if latency:
                self.results.append((name, ip, latency))
                if latency < min_latency:
                    best = (name, ip)
                    min_latency = latency
                self.log_status(f"→ {latency} ms")
            else:
                self.results.append((name, ip, "Timeout"))
                self.log_status("→ Timeout")

            self.progress["value"] = i
            self.root.update_idletasks()

        for _, ip, latency in self.results:
            self.tree.insert('', tk.END, values=(ip, latency))

        self.redraw_graph()

        if best:
            self.fastest_dns = best
            self.log_status(f"\nFastest DNS: {best[0]} ({best[1]}) - {min_latency} ms")
            self.prompt_dns_change(best[1])  # ✅ FIXED

        self.analyze_button.config(state="normal")

    # ✅ RESTORED DNS CHANGE FUNCTION
    def prompt_dns_change(self, dns_ip):
        response = messagebox.askyesno(
            "Change DNS Settings",
            f"Do you want to change your system DNS to {dns_ip}?",
        )
        if response:
            messagebox.showinfo("Info", f"DNS change simulated: {dns_ip}")

    # ✅ FIXED PDF EXPORT
    def export_to_pdf(self):
        filename = f"DNS_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        file_path = filedialog.asksaveasfilename(
            title="Save DNS Report",
            initialfile=filename,
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )

        if not file_path:
            return

        pdf = pdf_canvas.Canvas(file_path, pagesize=A4)
        pdf.setFont("Helvetica", 14)
        pdf.drawString(50, 800, "DNS Analyzer Tool Summary")

        pdf.setFont("Helvetica", 12)
        y = 770

        for name, ip, latency in self.results:
            text = f"{name} - {ip} -> {latency} ms" if isinstance(latency, float) else f"{name} - {ip} -> Timeout"
            pdf.drawString(50, y, text)
            y -= 20

        pdf.save()
        messagebox.showinfo("Success", "PDF exported successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = DNSAnalyzerApp(root)
    root.mainloop()