#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fibonacci Strategy Performance Report Launcher

This script provides a simple GUI to launch the Fibonacci Strategy Performance Report Generator.

Usage:
    python launch_fibonacci_report.py
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import webbrowser
from datetime import datetime


class FibonacciReportLauncher:
    """GUI application to launch the Fibonacci Strategy Performance Report Generator"""

    def __init__(self, root):
        """Initialize the application"""
        self.root = root
        self.root.title("Fibonacci Strategy Performance Report")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Set default values
        self.default_history_file = os.path.join("logs", "fibonacci_trades.json")
        self.default_output_dir = os.path.join("reports", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Create GUI elements
        self._create_widgets()
        self._center_window()
    
    def _create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Fibonacci Strategy Performance Report Generator",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # History file selection
        history_frame = tk.Frame(main_frame)
        history_frame.pack(fill=tk.X, pady=5)
        
        history_label = tk.Label(history_frame, text="Trade History File:", width=20, anchor="w")
        history_label.pack(side=tk.LEFT)
        
        self.history_var = tk.StringVar(value=self.default_history_file)
        history_entry = tk.Entry(history_frame, textvariable=self.history_var, width=40)
        history_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        history_button = tk.Button(history_frame, text="Browse", command=self._browse_history_file)
        history_button.pack(side=tk.RIGHT)
        
        # Output directory selection
        output_frame = tk.Frame(main_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        output_label = tk.Label(output_frame, text="Output Directory:", width=20, anchor="w")
        output_label.pack(side=tk.LEFT)
        
        self.output_var = tk.StringVar(value=self.default_output_dir)
        output_entry = tk.Entry(output_frame, textvariable=self.output_var, width=40)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        output_button = tk.Button(output_frame, text="Browse", command=self._browse_output_dir)
        output_button.pack(side=tk.RIGHT)
        
        # Options frame
        options_frame = tk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Open report checkbox
        self.open_report_var = tk.BooleanVar(value=True)
        open_report_check = tk.Checkbutton(
            options_frame,
            text="Open report when complete",
            variable=self.open_report_var
        )
        open_report_check.pack(anchor="w")
        
        # Buttons frame
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))
        
        generate_button = tk.Button(
            buttons_frame,
            text="Generate Report",
            command=self._generate_report,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10
        )
        generate_button.pack(side=tk.RIGHT)
        
        # Status frame
        status_frame = tk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.status_var = tk.StringVar(value="Ready to generate report")
        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            fg="#666",
            anchor="w"
        )
        status_label.pack(fill=tk.X)
    
    def _center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _browse_history_file(self):
        """Browse for trade history file"""
        filename = filedialog.askopenfilename(
            title="Select Trade History File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=os.path.dirname(self.history_var.get())
        )
        if filename:
            self.history_var.set(filename)
    
    def _browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=os.path.dirname(self.output_var.get())
        )
        if directory:
            self.output_var.set(directory)
    
    def _generate_report(self):
        """Generate the performance report"""
        history_file = self.history_var.get()
        output_dir = self.output_var.get()
        
        # Validate inputs
        if not os.path.exists(history_file):
            messagebox.showerror(
                "Error",
                f"Trade history file not found: {history_file}"
            )
            return
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Update status
        self.status_var.set("Generating report...")
        self.root.update()
        
        try:
            # Run the report generator script
            script_path = os.path.join("backend", "generate_fibonacci_performance_report.py")
            cmd = [
                sys.executable,
                script_path,
                "--history_file", history_file,
                "--output_dir", output_dir
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.status_var.set("Report generated successfully")
                messagebox.showinfo(
                    "Success",
                    f"Performance report generated successfully in {output_dir}"
                )
                
                # Open the report if requested
                if self.open_report_var.get():
                    report_file = os.path.join(output_dir, "fibonacci_performance_report.html")
                    if os.path.exists(report_file):
                        webbrowser.open(f"file://{os.path.abspath(report_file)}")
            else:
                self.status_var.set("Error generating report")
                messagebox.showerror(
                    "Error",
                    f"Failed to generate report:\n{stderr}"
                )
        except Exception as e:
            self.status_var.set("Error generating report")
            messagebox.showerror(
                "Error",
                f"An error occurred: {str(e)}"
            )


def main():
    """Main function to start the application"""
    root = tk.Tk()
    app = FibonacciReportLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()