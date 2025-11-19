#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for Financial Records Crawler
Verifies and sets up all dependencies including Glider, Chrome, and ChromeDriver
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.6 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 6):
        print("ERROR: Python 3.6 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_glider_repo():
    """Check if Glider repository is cloned"""
    glider_path = Path("glider")
    if not glider_path.exists():
        print("ERROR: Glider repository not found")
        print("Please run: git clone https://github.com/microsoft/glider_tasklet_crawler.git glider")
        return False
    print("✓ Glider repository found")
    return True


def install_python_packages():
    """Install required Python packages"""
    print("\nInstalling Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Python packages installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install Python packages: {e}")
        return False


def download_spacy_model():
    """Download spaCy English model"""
    print("\nDownloading spaCy English model...")
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_lg"])
        print("✓ spaCy model downloaded")
        return True
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Failed to download spaCy model: {e}")
        print("You may need to run: python -m spacy download en_core_web_lg")
        return False


def check_chrome():
    """Check if Chrome browser is installed"""
    system = platform.system()
    
    if system == "Windows":
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
    elif system == "Darwin":  # macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ]
    else:  # Linux
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium"
        ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✓ Chrome found at: {path}")
            return True
    
    print("WARNING: Chrome browser not found")
    print("Please install Google Chrome from https://www.google.com/chrome/")
    return False


def check_chromedriver():
    """Check if ChromeDriver is available"""
    system = platform.system()
    
    # Check in glider resources directory
    if system == "Windows":
        driver_name = "chromedriver_win32.exe"
    elif system == "Darwin":
        driver_name = "chromedriver_mac64"
    else:
        driver_name = "chromedriver_linux64"
    
    glider_driver_path = Path(f"glider/src/resources/{driver_name}")
    
    if glider_driver_path.exists():
        print(f"✓ ChromeDriver found at: {glider_driver_path}")
        return True
    
    # Check system PATH
    driver_name_simple = "chromedriver.exe" if system == "Windows" else "chromedriver"
    if shutil.which(driver_name_simple):
        print(f"✓ ChromeDriver found in system PATH")
        return True
    
    print("WARNING: ChromeDriver not found")
    print(f"Please download ChromeDriver from https://chromedriver.chromium.org/downloads")
    print(f"and place it at: {glider_driver_path}")
    print("Or install it via: pip install webdriver-manager")
    return False


def create_directories():
    """Create necessary directories"""
    directories = [
        "downloads",
        "data/tasks",
        "configs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directories created")
    return True


def main():
    """Main setup function"""
    print("=" * 60)
    print("Financial Records Crawler - Setup")
    print("=" * 60)
    
    checks = []
    
    # Check Python version
    checks.append(("Python Version", check_python_version()))
    
    # Check Glider repository
    checks.append(("Glider Repository", check_glider_repo()))
    
    # Create directories
    checks.append(("Directories", create_directories()))
    
    # Install Python packages
    if all(c[1] for c in checks[:2]):  # Only if Python and Glider are OK
        checks.append(("Python Packages", install_python_packages()))
        
        # Download spaCy model
        checks.append(("spaCy Model", download_spacy_model()))
    
    # Check Chrome
    checks.append(("Chrome Browser", check_chrome()))
    
    # Check ChromeDriver
    checks.append(("ChromeDriver", check_chromedriver()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Setup Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✓ Setup completed successfully!")
        print("\nYou can now run the crawler with:")
        print("  python financial_crawler.py <company_url>")
    else:
        print("\n⚠ Some checks failed. Please address the issues above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

