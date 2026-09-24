#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Launcher for Smart Calendar.
Provides cross-platform execution capabilities for Windows, Linux, and macOS.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_and_create_venv():
    """Check if virtual environment exists and offer to create it if not."""
    system = platform.system().lower()
    if system == "windows":
        venv_path = Path(".venv") / "Scripts" / "python.exe"
    else:
        venv_path = Path(".venv") / "bin" / "python"
    
    if not venv_path.exists():
        response = input("Virtual environment not found. Would you like to create one? (y/n): ")
        if response.lower() in ['y', 'yes']:
            print("Creating virtual environment...")
            try:
                subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
                print("Virtual environment created successfully.")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to create virtual environment: {e}")
                return False
        else:
            print("Proceeding with global Python installation...")
            return True
    else:
        print("Virtual environment found.")
        return True


def check_and_install_packages(use_venv=True):
    """Check for required packages and install them if missing."""
    system = platform.system().lower()
    if use_venv:
        if system == "windows":
            python_path = str(Path(".venv") / "Scripts" / "python.exe")
        else:
            python_path = str(Path(".venv") / "bin" / "python")
    else:
        python_path = sys.executable

    # Required packages for the Smart Calendar project
    required_packages = [
        "ttkbootstrap",  # Enhanced UI widgets
        "apscheduler",   # Background scheduling for event notifications
        "plyer",         # Cross-platform desktop notifications
        "tk",            # GUI toolkit (usually bundled with Python)
    ]

    print("\nRequired packages for Smart Calendar project:")
    print("- ttkbootstrap: Enhanced UI widgets")
    print("- apscheduler: Background scheduling for event notifications")
    print("- plyer: Cross-platform desktop notifications")
    print("- tk: GUI toolkit (usually bundled with Python)")
    
    response = input("\nWould you like to install these packages? (y/n): ")
    if response.lower() in ['y', 'yes']:
        try:
            # Upgrade pip first
            subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"], check=True)
            
            # Install required packages
            for package in required_packages:
                print(f"Installing {package}...")
                subprocess.run([python_path, "-m", "pip", "install", package], check=True)
            
            print("All required packages installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install packages: {e}")
            return False
    else:
        print("Skipping package installation. Make sure all required packages are installed manually.")
        return True


def main():
    print("\n=== Smart Calendar Application Setup ===\n")
    
    # Check if virtual environment exists or create one
    if not check_and_create_venv():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Ask if user wants to use virtual environment or global Python
    use_venv_response = input("\nWould you like to use the virtual environment? (y/n, default y): ").strip().lower()
    use_venv = use_venv_response in ['', 'y', 'yes']
    
    # Install required packages
    if not check_and_install_packages(use_venv):
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("\n=== Smart Calendar Application Launch ===\n")
    
    # Determine the Python executable path in the selected environment
    system = platform.system().lower()
    if use_venv:
        if system == "windows":
            venv_python = Path(".venv") / "Scripts" / "python.exe"
        else:
            venv_python = Path(".venv") / "bin" / "python"
    else:
        venv_python = Path(sys.executable)
    
    # Validate the existence of the Python executable
    if not venv_python.exists() and use_venv:
        print("Error: Selected Python environment not found!")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("Python environment found. Starting application...\n")
    
    # Execute the application
    try:
        result = subprocess.run([str(venv_python), "main.py"], check=True)
        print("\nApplication terminated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\nApplication startup error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()