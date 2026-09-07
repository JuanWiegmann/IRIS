"""
IRIS GUI Installer
==================

Modern graphical installer (no CMD window).

Features:
- Clean, minimal UI
- Real progress bar
- Prerequisites check
- Clone repo + run install.py

Build:
    pyinstaller --onefile --windowed --name=IRIS-Setup iris_gui_installer.py
"""

import sys
import subprocess
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox


# ═══════════════════════════════════════════════════════════
# IRIS INSTALLER GUI
# ═══════════════════════════════════════════════════════════

class IRISInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("IRIS Installer")
        self.root.geometry("600x450")
        self.root.resizable(False, False)

        # Modern colors
        self.bg_color = "#1a1a1a"
        self.fg_color = "#ffffff"
        self.accent_color = "#00d9ff"
        self.success_color = "#00ff88"
        self.error_color = "#ff4466"

        self.root.configure(bg=self.bg_color)

        self.install_dir = Path.home() / "IRIS"
        self.setup_ui()

    def setup_ui(self):
        """Create UI elements."""
        # Header
        header_frame = tk.Frame(self.root, bg=self.bg_color)
        header_frame.pack(pady=30)

        title = tk.Label(
            header_frame,
            text="IRIS",
            font=("Segoe UI", 32, "bold"),
            fg=self.accent_color,
            bg=self.bg_color
        )
        title.pack()

        subtitle = tk.Label(
            header_frame,
            text="( •‿• )",
            font=("Segoe UI", 20),
            fg=self.success_color,
            bg=self.bg_color
        )
        subtitle.pack()

        tagline = tk.Label(
            header_frame,
            text="Knowledge & Interaction Manager",
            font=("Segoe UI", 10),
            fg=self.fg_color,
            bg=self.bg_color
        )
        tagline.pack(pady=5)

        # Main content
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        # Status label
        self.status_label = tk.Label(
            content_frame,
            text="Ready to install",
            font=("Segoe UI", 11),
            fg=self.fg_color,
            bg=self.bg_color,
            anchor="w"
        )
        self.status_label.pack(fill=tk.X, pady=(0, 10))

        # Progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=self.bg_color,
            bordercolor=self.accent_color,
            background=self.accent_color,
            lightcolor=self.accent_color,
            darkcolor=self.accent_color
        )

        self.progress = ttk.Progressbar(
            content_frame,
            style="Custom.Horizontal.TProgressbar",
            length=520,
            mode='determinate',
            maximum=100
        )
        self.progress.pack(pady=10)

        # Install location
        location_frame = tk.Frame(content_frame, bg=self.bg_color)
        location_frame.pack(fill=tk.X, pady=20)

        location_label = tk.Label(
            location_frame,
            text=f"Install location: {self.install_dir}",
            font=("Segoe UI", 9),
            fg="#888888",
            bg=self.bg_color
        )
        location_label.pack()

        # Install button
        self.install_button = tk.Button(
            content_frame,
            text="Install IRIS",
            font=("Segoe UI", 12, "bold"),
            fg=self.bg_color,
            bg=self.accent_color,
            activebackground=self.success_color,
            activeforeground=self.bg_color,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.start_installation,
            width=20,
            height=2
        )
        self.install_button.pack(pady=20)

        # Details text
        self.details_text = tk.Text(
            content_frame,
            height=6,
            width=70,
            font=("Consolas", 8),
            bg="#0d0d0d",
            fg="#aaaaaa",
            relief=tk.FLAT,
            state=tk.DISABLED
        )
        self.details_text.pack(pady=10)

    def log(self, message, color=None):
        """Add message to details log."""
        self.details_text.config(state=tk.NORMAL)
        if color:
            self.details_text.insert(tk.END, f"{message}\n", color)
        else:
            self.details_text.insert(tk.END, f"{message}\n")
        self.details_text.see(tk.END)
        self.details_text.config(state=tk.DISABLED)
        self.root.update()

    def update_status(self, message, progress=None):
        """Update status label and progress bar."""
        self.status_label.config(text=message)
        if progress is not None:
            self.progress['value'] = progress
        self.root.update()

    def check_git(self):
        """Check if git is installed."""
        self.log("Checking Git...")
        try:
            subprocess.run(
                ["git", "--version"],
                capture_output=True,
                check=True,
                timeout=5
            )
            self.log("✓ Git found")
            return True
        except:
            self.log("✗ Git not found", "error")
            return False

    def check_python(self):
        """Check if Python is available."""
        self.log("Checking Python...")
        try:
            result = subprocess.run(
                [sys.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip()
            self.log(f"✓ {version}")
            return True
        except:
            self.log("✗ Python not found", "error")
            return False

    def clone_repo(self):
        """Clone IRIS repository."""
        self.log(f"Cloning to {self.install_dir}...")
        try:
            subprocess.run(
                ["git", "clone", "https://github.com/JuanWiegmann/IRIS.git", str(self.install_dir)],
                capture_output=True,
                check=True,
                timeout=120
            )
            self.log("✓ Repository cloned")
            return True
        except subprocess.TimeoutExpired:
            self.log("✗ Clone timeout", "error")
            return False
        except subprocess.CalledProcessError as e:
            self.log(f"✗ Clone failed: {e.stderr[:60] if e.stderr else 'unknown error'}", "error")
            return False

    def run_install(self):
        """Run install.py."""
        self.log("Running installation...")
        install_script = self.install_dir / "install.py"

        if not install_script.exists():
            self.log("✗ install.py not found", "error")
            return False

        try:
            # Run in subprocess, capture output
            process = subprocess.Popen(
                [sys.executable, str(install_script)],
                cwd=self.install_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Stream output
            for line in process.stdout:
                self.log(line.strip())

            process.wait(timeout=600)

            if process.returncode == 0:
                self.log("✓ Installation complete")
                return True
            else:
                self.log("✗ Installation failed", "error")
                return False

        except subprocess.TimeoutExpired:
            self.log("✗ Installation timeout", "error")
            return False
        except Exception as e:
            self.log(f"✗ Error: {str(e)[:60]}", "error")
            return False

    def start_installation(self):
        """Start installation process in background thread."""
        self.install_button.config(state=tk.DISABLED)

        def install_thread():
            try:
                # Step 1: Prerequisites (20%)
                self.update_status("Checking prerequisites...", 10)

                if not self.check_git():
                    messagebox.showerror(
                        "Git Not Found",
                        "Git is required. Install from:\nhttps://git-scm.com/download/win"
                    )
                    self.install_button.config(state=tk.NORMAL)
                    return

                self.update_status("Checking prerequisites...", 15)

                if not self.check_python():
                    messagebox.showerror("Python Not Found", "Python 3.11+ is required.")
                    self.install_button.config(state=tk.NORMAL)
                    return

                self.update_status("Prerequisites OK", 20)
                time.sleep(0.5)

                # Step 2: Clone (50%)
                self.update_status("Downloading IRIS...", 30)

                if not self.clone_repo():
                    messagebox.showerror("Clone Failed", "Could not download IRIS repository.")
                    self.install_button.config(state=tk.NORMAL)
                    return

                self.update_status("Download complete", 50)
                time.sleep(0.5)

                # Step 3: Install (100%)
                self.update_status("Installing components...", 60)

                if not self.run_install():
                    messagebox.showerror("Installation Failed", "Installation encountered errors.")
                    self.install_button.config(state=tk.NORMAL)
                    return

                self.update_status("Installation complete!", 100)

                # Success
                messagebox.showinfo(
                    "Success!",
                    "IRIS installed successfully!\n\n"
                    "Next: Start Claude Code and run /startIris"
                )

                self.root.quit()

            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error:\n{str(e)[:100]}")
                self.install_button.config(state=tk.NORMAL)

        thread = threading.Thread(target=install_thread, daemon=True)
        thread.start()


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    """Launch GUI installer."""
    root = tk.Tk()
    app = IRISInstaller(root)
    root.mainloop()


if __name__ == "__main__":
    main()
