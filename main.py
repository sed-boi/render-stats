# main.py
import bpy
import atexit
import os
import json
import urllib.request
import socket
import select
import platform
import subprocess

from bpy.types import Panel, Operator

# Import our custom modules
from .server import lowlevel_nat  # NAT mapping module using miniupnpc
from .stats import get_render_stats  # Returns current render stats (updated by our handlers)
from .utils import get_access_key     # Returns an access key

server_started = False
public_url = ""
server_socket = None
SERVER_PORT = 8080

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

def add_firewall_rule(port):
    system = platform.system()
    rule_name = "Blender Render Stats Addon"
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
        try:
            subprocess.check_call(["sudo", "ufw", "allow", f"{port}/tcp"])
            print("Firewall rule added using ufw on Linux.")
        except Exception as e:
            print("Failed to add firewall rule on Linux. Please add the rule manually.", e)
    elif system == "Darwin":
        print("On macOS, please ensure Blender is allowed to accept incoming connections on port", port)
    else:
        print("Unsupported OS for firewall automation.")

def remove_firewall_rule(port):
    system = platform.system()
    rule_name = "Blender Render Stats Addon"
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
        try:
            subprocess.check_call(["sudo", "ufw", "delete", "allow", f"{port}/tcp"])
            print("Firewall rule removed using ufw on Linux.")
        except Exception as e:
            print("Failed to remove firewall rule on Linux.", e)
    elif system == "Darwin":
        print("On macOS, please manually remove the firewall rule if needed.")
    else:
        print("Unsupported OS for firewall automation.")

def start_server_once():
    global server_started, public_url, server_socket
    if server_started:
        print("Server already started.")
        return

    add_firewall_rule(SERVER_PORT)

    ext_ip_buf = bytearray(64)
    ret = lowlevel_nat.SetupMapping(SERVER_PORT, ext_ip_buf, len(ext_ip_buf))
    if ret == 0:
        external_ip = ext_ip_buf.decode().strip('\x00')
    else:
        external_ip = get_public_ip()
        print("UPnP NAT mapping failed; falling back to public IP (port may not be forwarded).")
    
    access_key = get_access_key()
    if ":" in external_ip:
        public_url = f"http://[{external_ip}]:{SERVER_PORT}/?key={access_key}"
    else:
        public_url = f"http://{external_ip}:{SERVER_PORT}/?key={access_key}"
    print("Public URL:", public_url)

    generate_qr_code(public_url, "session_id_dummy")

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
        return

    server_started = True
    bpy.app.timers.register(process_requests)

def process_requests():
    global server_socket
    if server_socket is None:
        return None
    try:
        ready, _, _ = select.select([server_socket], [], [], 0)
        for s in ready:
            conn, addr = s.accept()
            handle_client(conn, addr)
    except Exception:
        pass
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
            # Serve the improved HTML UI with progress bar and log console.
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Render Status</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background-color: #f7f7f7;
      margin: 0;
      padding: 20px;
    }}
    #container {{
      max-width: 600px;
      margin: auto;
      background: #fff;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    h1, h2 {{
      text-align: center;
    }}
    .stat {{
      margin: 10px 0;
      font-size: 1.1em;
    }}
    #progressBarContainer {{
      width: 100%;
      background-color: #ddd;
      border-radius: 5px;
      margin: 10px 0;
    }}
    #progressBar {{
      width: 0%;
      height: 20px;
      background-color: #4caf50;
      border-radius: 5px;
      text-align: center;
      color: white;
      line-height: 20px;
      font-size: 0.9em;
    }}
    #logconsole {{
      background: #e8e8e8;
      padding: 10px;
      border-radius: 4px;
      font-family: monospace;
      white-space: pre-wrap;
      margin: 10px 0;
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid #ccc;
    }}
  </style>
</head>
<body>
  <div id="container">
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
      fetch('/stats')
        .then(response => response.json())
        .then(data => {{
          document.getElementById('current_frame').textContent = data.current_frame;
          document.getElementById('total_frames').textContent = data.total_frames;
          document.getElementById('last_frame_time').textContent = data.last_frame_time;
          document.getElementById('total_expected_time').textContent = data.total_expected_time;
          document.getElementById('render_active').textContent = data.render_active ? "Yes" : "No";

          // Update progress bar.
          let progress = data.progress_percentage || 0;
          let progressBar = document.getElementById('progressBar');
          progressBar.style.width = progress + '%';
          progressBar.textContent = progress.toFixed(2) + '%';

          // Update log console.
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
    global server_started, public_url, server_socket
    if server_started and server_socket:
        try:
            server_socket.close()
        except Exception as e:
            print("Error closing server socket:", e)
        from .server.lowlevel_nat import RemoveMapping
        RemoveMapping(SERVER_PORT)
        remove_firewall_rule(SERVER_PORT)
        server_started = False
        public_url = ""
        print("Server stopped.")
    else:
        print("Server is not running.")

def check_and_install_dependencies():
    import subprocess, sys
    try:
        import qrcode
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode"])
    try:
        import miniupnpc
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "miniupnpc"])

def generate_qr_code(url, session_id):
    try:
        import qrcode
    except ImportError:
        print("qrcode module not available.")
        return
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    temp_dir = bpy.app.tempdir
    qr_image_path = os.path.join(temp_dir, "session_qr_code.png")
    if os.path.exists(qr_image_path):
        os.remove(qr_image_path)
    img.save(qr_image_path)
    if "qr_code_image" in bpy.data.images:
        bpy.data.images.remove(bpy.data.images["qr_code_image"])
    try:
        qr_image = bpy.data.images.load(qr_image_path)
        bpy.context.scene.qr_code_image = qr_image
    except Exception as e:
        print("Error loading QR image:", e)

# --- UI Panel and Operators ---
class RenderProgressPanel(Panel):
    bl_idname = "FINALTEST_PT_render_progress"
    bl_label = "Render Status"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Render Status"

    def draw(self, context):
        layout = self.layout
        layout.operator("finaltest.install_dependencies", text="Activate (Install Dependencies)")
        layout.separator()
        if server_started:
            layout.operator("finaltest.stop_server", text="Stop Server")
            layout.label(text="Public URL:")
            layout.label(text=public_url, icon='URL')
            layout.operator("finaltest.copy_url", text="Copy URL")
            if hasattr(context.scene, "qr_code_image") and context.scene.qr_code_image:
                layout.template_ID_preview(context.scene, "qr_code_image", new="image.new", open="image.open")
        else:
            layout.operator("finaltest.start_server", text="Start Server")
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

class StartServerOperator(Operator):
    bl_idname = "finaltest.start_server"
    bl_label = "Start Server"
    def execute(self, context):
        start_server_once()
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

class InstallDependenciesOperator(Operator):
    bl_idname = "finaltest.install_dependencies"
    bl_label = "Activate (Install Dependencies)"
    def execute(self, context):
        check_and_install_dependencies()
        self.report({'INFO'}, "Dependencies installed.")
        return {'FINISHED'}

classes = (
    RenderProgressPanel,
    StartServerOperator,
    StopServerOperator,
    CopyURLToClipboardOperator,
    InstallDependenciesOperator,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.qr_code_image = bpy.props.PointerProperty(type=bpy.types.Image)
    atexit.register(stop_server)
    print("Render Stats Addon registered.")

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "qr_code_image"):
        del bpy.types.Scene.qr_code_image
    stop_server()
    print("Render Stats Addon unregistered.")

if __name__ == "__main__":
    register()
