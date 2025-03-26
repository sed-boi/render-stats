# Render Stats Addon

**Pre-release Version 1.0.0-beta**

The Render Stats Addon for Blender creates a lightweight HTTP server that automatically maps your NAT via UPnP and supports IPv6 connections. It serves a browser-friendly UI that displays live render statistics—including current frame, total frames, progress, and frame timing—via a progress bar and a log console that aggregates messages from your render pipeline.

This addon streamlines remote render monitoring by eliminating manual configuration steps. Simply start the addon, and it automatically generates a unique public URL (with a QR code) that you can open on any browser to track your render progress in real time.

> **Disclaimer:**  
> This addon is an independent project and is not affiliated with, endorsed by, or representing the Blender Foundation. Any errors or issues encountered while using this addon are solely the responsibility of the addon, not Blender.

## Limitations

**IPv6 Only:**  
Due to current limitations in some network environments (especially virtualized ones), the addon supports **only IPv6 connectivity**. The addon may generate an IPv4 public URL if no IPv6 connection is available; however, for full functionality—including NAT mapping and QR code generation—the network must support IPv6. Please ensure your environment (router/ISP) provides IPv6 connectivity. Dual‑stack (IPv4/IPv6) support is not available in this version.

## Important First-Time Setup

**Before you Start Server, please click the "Activate (Install Dependencies)" button in the addon’s UI panel.**

This step installs all required Python modules (such as `qrcode`, `Pillow` for the `PIL` package, and `miniupnpc`) into the addon’s vendor folder.
**Without this activation, you might encounter errors like:** 
  ```
     ModuleNotFoundError: No module named 'qrcode'
     
     or
     
     ModuleNotFoundError: No module named 'PIL'
     
```
These errors indicate that the addon’s dependencies have not been installed, and the QR code will not be generated. Please activate dependencies before running your project.

**Important:** Please ensure you click the **"Enable IPv6"** button in the addon's UI panel every time before you click **"Start Server"**. This step ensures that the addon attempts to establish an IPv6 connection for the server.

## Creator

*Made for creators by a creator.*  
Developed by **Vishal Chaudhary** – [sedboi.com](https://www.sedboi.com)

## Features

- **Dynamic Render Statistics:**  
  Uses Blender’s render post handler to update live data after each rendered frame.

- **Browser-friendly UI:**  
  Serves an HTML page featuring a responsive progress bar, detailed log console, and live render statistics that refresh every second.

- **NAT Mapping & UPnP  :**  
  Utilizes UPnP (via miniupnpc) to set up real port mappings and creates an IPv6 socket so that your local HTTP server is exposed automatically without extra configuration.

- **Automatic QR Code Generation:**  
  Generates a unique QR code from the public URL so that you can easily monitor render status on any device.

- **Custom Logging:**  
  Implements a custom logging mechanism using Python’s logging module that aggregates messages (asset loading, BVH generation, compositing, errors, etc.) into a log console for real-time debugging.

## Evolution of the Addon

Originally, this addon was designed to work with AWS Lambda and S3 for remote monitoring of render progress. However, this approach required manual configuration and additional setup from users. After extensive testing, we transitioned to a more user-friendly method that leverages IPv6. This new approach requires zero manual configuration—your local Blender machine automatically exposes a secure HTTP channel using UPnP, and the render status is accessible via a unique public URL with an embedded access key.

## Installation

1. **Download and Install the Addon:**
   - Clone this repository or download it as a ZIP.
   - In Blender, open **Edit > Preferences > Add-ons**.
   - Click **Install...** and select the downloaded ZIP file or folder containing the addon.
   - Enable the addon by checking its box.

2. **Initial Dependency Setup (First Use):**
   - **Before using the addon for any render project, click the "Activate (Install Dependencies)" button in the addon’s UI panel.**
   - This will automatically install required Python modules (`qrcode`, `Pillow`, `miniupnpc`) into the addon’s vendor folder.
   - After activating dependencies, restart Blender if necessary.

## Usage

1. **Start the Server:**
   - In the 3D View sidebar under the **Render Status** tab, click **Start Server**.
   - The addon will automatically:
     - Map your NAT via UPnP.
     - Create an IPv6/dual‑stack socket.
     - Add necessary firewall rules (if required on your OS).
     - Generate a unique public URL and QR code.

2. **Monitor Your Render:**
   - Open the generated URL in any web browser (or scan the QR code with your mobile device).
   - The webpage displays:
     - A responsive progress bar indicating render progress.
     - Live render statistics (current frame, total frames, last frame time, total expected time, etc.).
     - A log console with detailed render pipeline messages.

3. **Stop the Server:**
   - When finished, click **Stop Server** in the addon’s UI panel to shut down the HTTP server and remove any firewall/NAT mappings.

4. **Icon-Based Status Indicators:**
   Displays the status of Dependencies, IPv6, and the Server using Blender's built-in icons(🟥,🟨,🟩).
   **Represents:**
   - Dependencies : 🟥(Dependencies not installed), 🟩(Dependencies Installed).
   - Ipv6: 🟥(Ipv6 Not ready to use), 🟩(Ipv6 Ready to use).
   - Server: 🟥(Server OFF), 🟨(Server is ON and waiting for connection), 🟩(Server is ON and User is Connected).

>Note: Activate dependencies before Starting server,
Start server before you start rendering to keep things smooth.
The data is sent after frame completion,
so if your single frame takes 10 minutes then the latest update will be sent in 10 minutes and so on.
This might show a delay for first two frames,
it is advised to wait for at least 2 frames to get rendered, in order to confirm the data sent is accurate.  

![Untitled design (1)](https://github.com/user-attachments/assets/a60c55e9-a77f-4a5f-bc08-1a52b3eb798c)

 
 

## FAQ

**Q: Do I need to configure AWS or any external services?**  
A: No. We initially explored an AWS-based solution, but switched to using IPv6 and dual‑stack NAT mapping for a completely zero‑user configuration.

**Q: Which Blender versions are supported?**  
A: While the addon works on lower Blender versions, Blender 4.3+ is recommended for optimal performance and full feature support.

**Q: What if my firewall blocks the port?**  
A: The addon attempts to add firewall rules automatically on Windows and Linux. On macOS, you may need to manually allow incoming connections on port 8080.

**Q: Why am I seeing a "ModuleNotFoundError" related to dependencies?**  
A: If you haven’t clicked the **Activate (Install Dependencies)** button before running the addon, required Python modules (like `qrcode` and `Pillow`) might not be installed, leading to errors such as:
```
     ModuleNotFoundError: No module named 'qrcode'
     
     or
     
     ModuleNotFoundError: No module named 'PIL'
     
```
Please activate dependencies first.

**Q: How does the addon capture and display render logs?**  
A: A custom logging mechanism aggregates log messages (asset loading, BVH generation, compositing, errors, etc.) using Python’s logging module and displays them in a log console on the web UI.

**Q: Who is responsible for issues with this addon?**  
A: This addon is an independent project and is not affiliated with the Blender Foundation. Any issues or errors are solely the responsibility of the addon.

## Contributing

Contributions, bug reports, and feature requests are welcome. Please open an issue or submit a pull request with your changes. When contributing, ensure that your modifications are well documented and follow the project’s coding style.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

