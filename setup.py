import os
import sys
import subprocess
import shutil

def install_dependencies():
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def create_executable():
    print("Creating executable...")
    subprocess.check_call([
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=TEX-NAV",
        "--icon=tex_nav_icon.ico",
        "tex_nav.py"
    ])

def copy_executable():
    print("Copying executable to installation directory...")
    install_dir = os.path.expanduser("~\\TEX-NAV")
    os.makedirs(install_dir, exist_ok=True)
    shutil.copy2("dist\\TEX-NAV.exe", install_dir)

def create_shortcut():
    print("Creating desktop shortcut...")
    desktop = os.path.expanduser("~\\Desktop")
    shortcut_path = os.path.join(desktop, "TEX-NAV.lnk")
    install_dir = os.path.expanduser("~\\TEX-NAV")
    exe_path = os.path.join(install_dir, "TEX-NAV.exe")
    
    with open("create_shortcut.vbs", "w") as f:
        f.write(f'Set oWS = WScript.CreateObject("WScript.Shell")\n')
        f.write(f'sLinkFile = "{shortcut_path}"\n')
        f.write(f'Set oLink = oWS.CreateShortcut(sLinkFile)\n')
        f.write(f'oLink.TargetPath = "{exe_path}"\n')
        f.write(f'oLink.Save\n')
    
    subprocess.call(["cscript", "create_shortcut.vbs"])
    os.remove("create_shortcut.vbs")

def main():
    install_dependencies()
    create_executable()
    copy_executable()
    create_shortcut()
    print("TEX-NAV has been successfully installed!")
    print("You can find the executable in your home directory under the 'TEX-NAV' folder.")
    print("A shortcut has been created on your desktop.")

if __name__ == "__main__":
    main()
