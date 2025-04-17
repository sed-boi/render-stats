# main.py
import bpy
import atexit
import os
import sys
import json
import urllib.request
import socket
import select
import platform
import subprocess
import shutil
import time
from urllib.parse import urlparse, parse_qs

# Determine add-on directory and lib folder path
addon_dir = os.path.dirname(__file__)
lib_path = os.path.join(addon_dir, "lib")
if not os.path.exists(lib_path):
    os.makedirs(lib_path)
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)
    print("Added lib folder to sys.path:", lib_path)

from bpy.types import Panel, Operator

# Import our custom modules
from .server import lowlevel_nat  # NAT mapping module using miniupnpc (from lib)
from .stats import get_render_stats  # Returns current render stats (updated by our handlers)
from .utils import get_access_key     # Returns a secure 16-character access key

# Global variables
server_started = False
public_url = ""
server_socket = None
SERVER_PORT = 8080
access_key = ""
dependencies_activated = False  # Will be set via the dependency activation operator
addon_preferences = None
ipv6_enabled = False
server_connecting = False
client_connected = False
start_server_error = ""

# Color codes (not directly usable for label text color)
GREEN = "#00FF00"
RED = "#FF0000"
YELLOW = "#FFFF00"

def get_dot(status, for_server=False):
    if for_server:
        if server_started:
            if client_connected:
                return "STRIP_COLOR_04"  # Green tick when client is connected
            else:
                return "STRIP_COLOR_03"  # Red tick (representing yellow wait) when waiting
        else:
            return "STRIP_COLOR_01"  # Red cross when stopped
    else:
        return "STRIP_COLOR_04" if status else "STRIP_COLOR_01" # Green tick if true, Red cross if false

def update_render_progress_data():
    return get_render_stats()

def get_public_ip():
    try:
        with urllib.request.urlopen("https://api64.ipify.org?format=json") as response:
            data = response.read()
            ip_info = json.loads(data.decode("utf-8"))
            return ip_info["ip"]
    except Exception as e:
        print("Error obtaining public IP:", e)
        return "::1"

def try_enable_ipv6():
    """Attempt to enable IPv6 automatically (only for Windows)."""
    system = platform.system()
    if system == "Windows":
        try:
            subprocess.check_call(["netsh", "interface", "ipv6", "set", "interface", "1", "enabled"])
            print("IPv6 enabled on Windows.")
            return True
        except Exception as e:
            print("Failed to enable IPv6 on Windows:", e)
            return False
    elif system in ("Linux", "Darwin"):
        # Auto-enable is not attempted on Linux/macOS
        return False
    else:
        return False

def add_firewall_rule(port):
    system = platform.system()
    rule_name = "Render Stats Addon"
    if system == "Windows":
        cmd = [
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={rule_name}",
            "dir=in",
            "action=allow",
            "protocol=TCP",
            f"localport={port}"
        ]
        try:
            subprocess.check_call(cmd, shell=True)
            print("Firewall rule added on Windows.")
        except Exception as e:
            print("Failed to add firewall rule on Windows. Run Blender as Administrator.", e)
    elif system == "Linux":
        cmd = ["sudo", "ufw", "allow", f"{port}/tcp"]
        try:
            subprocess.check_call(cmd)
            print("Firewall rule added using ufw on Linux.")
        except Exception as e:
            print("Failed to add firewall rule on Linux. Please add the rule manually.", e)
    elif system == "Darwin":
        blender_executable = sys.executable
        cmd = f"/usr/libexec/ApplicationFirewall/socketfilterfw --add \"{blender_executable}\""
        try:
            subprocess.check_call(["osascript", "-e", f'do shell script "{cmd}" with administrator privileges'])
            print("Firewall rule added on macOS.")
        except Exception as e:
            print("Failed to add firewall rule on macOS:", e)
    else:
        print("Unsupported OS for firewall automation.")

def remove_firewall_rule(port):
    system = platform.system()
    rule_name = "Render Stats Addon"
    if system == "Windows":
        cmd = [
            "netsh", "advfirewall", "firewall", "delete", "rule",
            f"name={rule_name}",
            "protocol=TCP",
            f"localport={port}"
        ]
        try:
            subprocess.check_call(cmd, shell=True)
            print("Firewall rule removed on Windows.")
        except Exception as e:
            print("Failed to remove firewall rule on Windows.", e)
    elif system == "Linux":
        cmd = ["sudo", "ufw", "delete", "allow", f"{port}/tcp"]
        try:
            subprocess.check_call(cmd)
            print("Firewall rule removed using ufw on Linux.")
        except Exception as e:
            print("Failed to remove firewall rule on Linux.", e)
    elif system == "Darwin":
        blender_executable = sys.executable
        cmd = f"/usr/libexec/ApplicationFirewall/socketfilterfw --remove \"{blender_executable}\""
        try:
            subprocess.check_call(["osascript", "-e", f'do shell script "{cmd}" with administrator privileges'])
            print("Firewall rule removed on macOS.")
        except Exception as e:
            print("Failed to remove firewall rule on macOS:", e)
    else:
        print("Unsupported OS for firewall automation.")

def start_server_once():
    global server_started, public_url, server_socket, access_key, dependencies_activated, ipv6_enabled, start_server_error, server_connecting
    start_server_error = ""
    if not dependencies_activated:
        print("Error: Dependencies not activated. Please click 'Activate Dependencies' first.")
        start_server_error = "Dependencies not activated. Please click 'Activate Dependencies' first."
        return
    if not ipv6_enabled:
        print("Error: IPv6 is not enabled. Kindly enable IPv6 before starting the server.")
        start_server_error = "Kindly enable IPv6 before starting server."
        return
    if server_started:
        print("Server already started.")
        return

    server_connecting = True
    add_firewall_rule(SERVER_PORT)

    # Attempt NAT mapping via UPnP
    ext_ip_buf = bytearray(64)
    try:
        ret = lowlevel_nat.SetupMapping(SERVER_PORT, ext_ip_buf, len(ext_ip_buf))
    except Exception as e:
        if str(e).strip() == "Success":
            ret = 0
            print("UPnP discovery returned 'Success' exception; treating as success.")
        else:
            print("Error during UPnP mapping:", e)
            ret = -1

    if ret == 0:
        external_ip = ext_ip_buf.decode().strip('\x00')
        if not external_ip:  # Fallback if UPnP returns an empty IP
            external_ip = get_public_ip()
            print("External IP from UPnP was empty; using public IP instead:", external_ip)
    else:
        external_ip = get_public_ip()
        print("UPnP NAT mapping failed; falling back to public IP (port may not be forwarded).")

    access_key = get_access_key()
    public_url = f"http://[{external_ip}]:{SERVER_PORT}/?key={access_key}"
    print("Public URL:", public_url)

    generate_qr_code(public_url)

    try:
        server_socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        try:
            server_socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except Exception as e:
            print("Could not disable IPv6-only mode:", e)
        server_socket.setblocking(False)
        server_socket.bind(('', SERVER_PORT))
        server_socket.listen(5)
    except Exception as e:
        print("Error setting up server socket:", e)
        server_connecting = False
        return

    global client_connected
    client_connected = False
    server_started = True
    server_connecting = False
    bpy.app.timers.register(process_requests)

def process_requests():
    global server_socket, client_connected
    if server_socket is None:
        return None
    try:
        ready, _, _ = select.select([server_socket], [], [], 0)
        for s in ready:
            conn, addr = s.accept()
            client_connected = True
            handle_client(conn, addr)
    except Exception as e:
        print("Error in process_requests:", e)
    return 0.1

def handle_client(conn, addr):
    try:
        conn.settimeout(1.0)
        request = b""
        while True:
            data = conn.recv(1024)
            if not data:
                break
            request += data
            if b"\r\n\r\n" in request:
                break

        request_line = request.split(b"\r\n")[0].decode('utf-8')
        parsed_url = urlparse(request_line.split(" ")[1])
        qs = parse_qs(parsed_url.query)
        received_key = qs.get("key", [None])[0]
        if received_key != access_key:
            response = ("HTTP/1.1 403 Forbidden\r\n"
                        "Content-Type: text/plain\r\n"
                        "Connection: close\r\n"
                        "\r\nForbidden")
            conn.sendall(response.encode('utf-8'))
            return

        if request_line.startswith("GET /stats"):
            stats = update_render_progress_data()
            stats_json = json.dumps(stats)
            response_body = stats_json.encode('utf-8')
            response_header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode('utf-8')
            conn.sendall(response_header + response_body)
        else:
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Render Status</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #000;
            color: #fff;
            margin: 0;
            padding: 20px;
        }}
        #container {{
            max-width: 600px;
            width: 90%;
            margin: auto;
            background: #111;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(255,255,255,0.1);
        }}
        h1, h2 {{
            text-align: center;
            margin: 0.5em 0;
        }}
        .header-banner a {{
            text-decoration: none;
            color: inherit;
        }}
        .header-banner {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .header-banner img {{
            width: 80px;
            height: auto;
            display: block;
            margin: 10px auto 0;
        }}
        .stat {{
            margin: 10px 0;
            font-size: 1.1em;
        }}
        #progressBarContainer {{
            width: 100%;
            background-color: #333;
            border-radius: 5px;
            margin: 10px 0;
        }}
        #progressBar {{
            width: 0%;
            height: 20px;
            background-color: #4caf50;
            border-radius: 5px;
            text-align: center;
            color: #000;
            line-height: 20px;
            font-size: 0.9em;
        }}
        #logconsole {{
            background: #222;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            white-space: pre-wrap;
            margin: 10px 0;
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #444;
        }}
        @media screen and (max-width: 600px) {{
            #container {{
                padding: 15px;
            }}
            .stat {{
                font-size: 1em;
            }}
            #progressBar {{
                height: 18px;
                line-height: 18px;
                font-size: 0.8em;
            }}
            .header-banner img {{
                width: 60px;
            }}
        }}
    </style>
</head>
<body>
    <div id="container">
        <div class="header-banner">
            <a href="https://www.sedboi.com" target="_blank">
                <h1>Made for creators by a creator</h1>
                <img src="https://static.wixstatic.com/media/279b0c_aa034e8acd1e40ada17a82e7a6160c14~mv2.png" alt="Creator Logo">
            </a>
        </div>
        <h1>Render Status</h1>
        <div class="stat">Current Frame: <span id="current_frame"></span> / <span id="total_frames"></span></div>
        <div id="progressBarContainer">
            <div id="progressBar">0%</div>
        </div>
        <div class="stat">Last Frame Time: <span id="last_frame_time"></span> s</div>
        <div class="stat">Total Expected Time: <span id="total_expected_time"></span> s</div>
        <div class="stat">Render Active: <span id="render_active"></span></div>
        <h2>Log Console</h2>
        <div id="logconsole">Loading logs...</div>
    </div>
    <script>
        function fetchStats() {{
            fetch('/stats?key={access_key}')
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('current_frame').textContent = data.current_frame;
                    document.getElementById('total_frames').textContent = data.total_frames;
                    document.getElementById('last_frame_time').textContent = data.last_frame_time;
                    document.getElementById('total_expected_time').textContent = data.total_expected_time;
                    document.getElementById('render_active').textContent = data.render_active ? "Yes" : "No";
                    let progress = data.progress_percentage || 0;
                    let progressBar = document.getElementById('progressBar');
                    progressBar.style.width = progress + '%';
                    progressBar.textContent = progress.toFixed(2) + '%';
                    document.getElementById('logconsole').textContent = data.log;
                }})
                .catch(error => console.error('Error fetching stats:', error));
        }}
        setInterval(fetchStats, 1000);
        fetchStats();
    </script>
</body>
</html>
"""
            response_body = html_content.encode('utf-8')
            response_header = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode('utf-8')
            conn.sendall(response_header + response_body)
    except Exception as e:
        print("Error handling client:", e)
    finally:
        conn.close()

def stop_server():
    global server_started, public_url, server_socket, client_connected, server_connecting
    if server_started and server_socket:
        try:
            server_socket.close()
            server_socket = None
        except Exception as e:
            print("Error closing server socket:", e)
        try:
            from .server.lowlevel_nat import RemoveMapping
            RemoveMapping(SERVER_PORT)
        except Exception as e:
            print("Error removing port mapping:", e)
        remove_firewall_rule(SERVER_PORT)
        server_started = False
        public_url = ""
        client_connected = False
        server_connecting = False
        print("Server stopped.")
    else:
        print("Server is not running.")

def check_and_install_dependencies():
    import subprocess, sys, os, shutil, time
    global dependencies_activated
    addon_dir = os.path.dirname(__file__)
    lib_path = os.path.join(addon_dir, "lib")
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)
        print("Added lib folder to sys.path:", lib_path)

    def install_package(package_name):
        try:
            print(f"Installing {package_name} into {lib_path} ...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "--target", lib_path])
            print(f"{package_name} installed successfully.")
        except Exception as e:
            print(f"Error installing {package_name}:", e)

    try:
        import qrcode
    except ImportError:
        install_package("qrcode")

    try:
        import miniupnpc
    except ImportError:
        install_package("miniupnpc")

    pil_path_target = os.path.join(lib_path, "PIL")
    if not os.path.exists(pil_path_target):
        install_package("Pillow")
        pil_path_root = os.path.join(addon_dir, "PIL")
        if os.path.exists(pil_path_root):
            try:
                shutil.move(pil_path_root, pil_path_target)
                print("Moved PIL folder from addon root to lib folder.")
            except Exception as e:
                print("Error moving PIL folder:", e)
    else:
        print("PIL package found in lib folder.")

    if platform.system() == "Linux":
        external_ip = get_public_ip()
        if "." in external_ip:
            print("IPv4 detected during dependency activation on Linux. "
                  "Auto-enable of IPv6 is not supported on Linux. "
                  "Please manually enable IPv6 or contact the author.")
    dependencies_activated = True
    if addon_preferences:
        addon_preferences.dependencies_activated = True
    print("Dependencies check complete. All required dependencies are installed, and IPv6 is set (if available).")

def generate_qr_code(public_url):
    try:
        import qrcode
    except ImportError:
        print("qrcode module not available.")
        return
    print("Generating QR code for URL:", public_url)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(public_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_dir = os.path.join(addon_dir, "temp_qr")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    qr_image_path = os.path.join(temp_dir, "session_qr_code.png")
    qr_image_path = os.path.normpath(qr_image_path)
    if os.path.exists(qr_image_path):
        os.remove(qr_image_path)
    try:
        img.save(qr_image_path)
        print("QR code image saved to:", qr_image_path)
    except Exception as e:
        print("Error saving QR code image:", e)
        return
    if "qr_code_image" in bpy.data.images:
        bpy.data.images.remove(bpy.data.images["qr_code_image"])
    try:
        qr_image = bpy.data.images.load(qr_image_path)
        bpy.context.scene.qr_code_image = qr_image
        print("QR code generated and loaded successfully.")
    except Exception as e:
        print("Error loading QR image:", e)

# --- UI Panel and Operators ---
class RenderProgressPanel(Panel):
    bl_idname = "PT_render_progress"
    bl_label = "Render Status"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Render Status"

    def draw(self, context):
        layout = self.layout

        # Display status indicators (with icons)
        row = layout.row(align=True)
        sub_row = row.row(align=True)
        sub_row.label(text="Dependencies:")
        sub_row.label(icon=get_dot(addon_preferences.dependencies_activated if addon_preferences else dependencies_activated))

        sub_row = row.row(align=True)
        sub_row.label(text="IPv6:")
        sub_row.label(icon=get_dot(ipv6_enabled))

        sub_row = row.row(align=True)
        sub_row.label(text="Server:")
        sub_row.label(icon=get_dot(server_started, for_server=True))

        layout.separator()
        # Operator buttons with dot prefix
        col = layout.column(align=True)
        row = col.row(align=True)
        row.enabled = not (addon_preferences.dependencies_activated if addon_preferences else dependencies_activated)
        row.operator("finaltest.activate_dependencies", text="● Activate Dependencies")

        row = col.row(align=True)
        row.operator("finaltest.enable_ipv6", text="● Enable IPv6")

        row = col.row(align=True)
        if not server_started:
            row.enabled = ipv6_enabled and (addon_preferences.dependencies_activated if addon_preferences else dependencies_activated)
            row.operator("finaltest.start_server", text="● Start Server")
        else:
            col.active_default = True
            row.operator("finaltest.stop_server", text="● Stop Server")
            col.active_default = False # Reset for other buttons

        if start_server_error:
            layout.label(text=f"<span style='color:{RED};'>{start_server_error}</span>", translate=False)

        if server_started:
            layout.separator()
            layout.label(text="Public URL:")
            layout.label(text=public_url, icon='URL')
            layout.operator("finaltest.copy_url", text="● Copy URL")
            if hasattr(context.scene, "qr_code_image") and context.scene.qr_code_image:
                layout.template_ID_preview(context.scene, "qr_code_image", new="image.new", open="image.open")

        layout.separator()
        stats = update_render_progress_data()
        layout.label(text=f"Current Frame: {stats.get('current_frame', 0)}")
        layout.label(text=f"Total Frames: {stats.get('total_frames', 0)}")
        layout.label(text=f"Progress: {stats.get('progress_percentage', 0):.2f}%")
        layout.label(text=f"Last Frame Time: {stats.get('last_frame_time', 0):.2f} s")
        layout.label(text=f"Total Expected Time: {stats.get('total_expected_time', 0):.2f} s")
        layout.label(text=f"Render Active: {'Yes' if stats.get('render_active', False) else 'No'}")
        layout.separator()
        layout.label(text="Log Console:")
        layout.label(text=stats.get("log", ""), icon='TEXT')

class ActivateDependenciesOperator(Operator):
    bl_idname = "finaltest.activate_dependencies"
    bl_label = "Activate Dependencies"
    def execute(self, context):
        check_and_install_dependencies()
        global dependencies_activated
        dependencies_activated = True
        self.report({'INFO'}, "Dependencies installed.")
        return {'FINISHED'}

class EnableIPv6Operator(Operator):
    bl_idname = "finaltest.enable_ipv6"
    bl_label = "Enable IPv6"
    def execute(self, context):
        global ipv6_enabled
        ipv6_enabled = True
        #  perform a check here.
        # For now, we just set the flag.
        self.report({'INFO'}, "IPv6 enabled.")
        return {'FINISHED'}

class StartServerOperator(Operator):
    bl_idname = "finaltest.start_server"
    bl_label = "Start Server"
    def execute(self, context):
        start_server_once()
        if start_server_error:
            self.report({'ERROR'}, f"Server could not start: {start_server_error}")
        else:
            self.report({'INFO'}, "Server started.")
        return {'FINISHED'}

class StopServerOperator(Operator):
    bl_idname = "finaltest.stop_server"
    bl_label = "Stop Server"
    def execute(self, context):
        stop_server()
        self.report({'INFO'}, "Server stopped.")
        return {'FINISHED'}

class CopyURLToClipboardOperator(Operator):
    bl_idname = "finaltest.copy_url"
    bl_label = "Copy URL"
    def execute(self, context):
        if public_url:
            context.window_manager.clipboard = public_url
            self.report({'INFO'}, "URL copied to clipboard.")
        return {'FINISHED'}

classes = (
    RenderProgressPanel,
    StartServerOperator,
    StopServerOperator,
    CopyURLToClipboardOperator,
    ActivateDependenciesOperator,
    EnableIPv6Operator,
)

def register():
    global addon_preferences, dependencies_activated
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.qr_code_image = bpy.props.PointerProperty(type=bpy.types.Image)
    atexit.register(stop_server)
    addon_preferences = bpy.context.preferences.addons[__package__].preferences
    dependencies_activated = addon_preferences.dependencies_activated
    print(f"Render Stats Addon registered with dependencies_activated = {dependencies_activated}")

def unregister():
    global addon_preferences, dependencies_activated, ipv6_enabled, server_started, client_connected, server_connecting, start_server_error
    for cls in classes:
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "qr_code_image"):
        del bpy.types.Scene.qr_code_image
    stop_server()
    if addon_preferences is not None:
        addon_preferences.dependencies_activated = dependencies_activated
    ipv6_enabled = False
    server_started = False
    client_connected = False
    server_connecting = False
    start_server_error = ""
    print("Render Stats Addon unregistered.")

if __name__ == "__main__":
    register()
