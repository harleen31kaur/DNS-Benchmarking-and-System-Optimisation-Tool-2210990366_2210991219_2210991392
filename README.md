# DNS Benchmarking and System Optimization Tool

## Team Details

1. Akira Singh 2210991219
2. Harleen Kaur 2210990366
3. Aryan Thakur 2210991392
   
Type: Copyright \
Current Status : Waiting
---
# Description
A cross-platform desktop application built with Python and Tkinter to benchmark DNS servers, compare latency, monitor DNS performance in real-time, export reports, and apply the fastest DNS settings.

---

# Features

* DNS latency benchmarking
* Live DNS monitoring mode
* Apply fastest DNS automatically
* Add and remove custom DNS servers
* Dark and Light theme support
* Graphical latency visualization
* Export reports as:

  * PDF
  * CSV
  * Excel (.xlsx)
* Cross-platform support:

  * Windows
  * macOS
  * Linux

---

# Default DNS Servers

* Google DNS → 8.8.8.8
* Cloudflare DNS → 1.1.1.1
* OpenDNS → 208.67.222.222
* Quad9 → 9.9.9.9

---

# Technologies Used

* Python
* Tkinter
* Matplotlib
* OpenPyXL
* ReportLab
* PyInstaller

---

# Running the Project from Source Code

## Prerequisites

Install:

* Python 3.10 or higher
* pip

Verify installation:

```bash
python --version
pip --version
```

---

# Step 1: Clone the Repository

```bash
git clone https://github.com/harleen31kaur/DNS-Benchmarking-and-System-Optimisation-Tool.git
```

Move into the project folder:

```bash
cd DNS-Benchmarking-and-System-Optimisation-Tool
```

---

# Step 2: Install Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

If requirements.txt is unavailable, install manually:

```bash
pip install matplotlib openpyxl reportlab
```

---

# Step 3: Run the Application

Run:

```bash
python main.py
```

The GUI application will launch.

---

# Running Using Executables

Prebuilt executables are available in the GitHub Releases section.

Download the appropriate package based on your operating system.

---

# Windows Executable

## Download

Download:

* `.exe` installer or executable

from the Releases section.

---

## Steps to Run on Windows

### Option 1: Using Installer

1. Download the Windows installer
2. Double-click the installer
3. Follow the installation steps
4. Launch the application from:

   * Desktop shortcut
   * Start Menu

---

### Option 2: Using Portable `.exe`

1. Download the `.exe` file
2. Extract if compressed
3. Double-click:

```bash
DNSAnalyzer.exe
```

---

# macOS Application

## Download

Download:

* `.app`

from the Releases section.

---

# Steps to Run on macOS

1. Download the `.app` package
2. Extract if zipped
3. Drag the application into the Applications folder
4. Open the application

---

# Linux Package

## Download

Download the Linux package from the Releases section.

After extracting the ZIP file, you will get a file named:

```bash
main
```

---

# Steps to Run on Linux

## Step 1: Open Terminal in Extracted Folder

Navigate to the folder containing the `main` file.

---

## Step 2: Make the File Executable

Run:

```bash
chmod +x main
```

---

## Step 3: Run the Application

Run:

```bash
./main
```

The DNS Analyzer application will launch.

---

# DNS Permission Requirements

Applying DNS settings requires administrator privileges.

## Windows

The application automatically requests Administrator access.

---

## macOS

The application may request sudo permissions.

---

## Linux

The application may require:

```bash
sudo
```

for modifying DNS settings.

---

# Export Features

The application supports exporting benchmark results in:

* PDF
* CSV
* Excel (.xlsx)

Use:

```text
Control Panel → Export
```

---

# Live Monitoring Mode

Enable:

```text
Live Mode
```

to continuously benchmark DNS latency every few seconds.

---
