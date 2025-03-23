# Render Stats Addon

The Render Stats Addon for Blender creates a lightweight HTTP server that automatically maps your NAT via UPnP and supports IPv6/dual‑stack connections. It serves a browser-friendly UI that displays live render statistics—including current frame, total frames, progress, and frame timing—via a progress bar and log console that aggregates messages from your render pipeline.

This addon streamlines remote render monitoring by eliminating manual configuration steps. Simply start the addon, and it automatically generates a unique public URL (with a QR code) that you can open on any browser to track your render progress in real time.

> **Disclaimer:**  
> This addon is an independent project and is not affiliated with, endorsed by, or representing the Blender Foundation. Any errors or issues encountered while using this addon are solely the responsibility of the addon itself, not Blender.

## Features

- **Dynamic Render Statistics:**  
  Uses Blender’s render post handler to update live data after every rendered frame.

- **Browser-friendly UI:**  
  Serves an HTML page featuring a progress bar, detailed log console, and updated render stats that refresh every second.

- **NAT Mapping & Dual‑Stack Support:**  
  Utilizes UPnP (via miniupnpc) to set up real port mappings and creates an IPv6 socket (dual‑stack if available) to automatically expose your local HTTP server.

- **Automatic QR Code Generation:**  
  Generates a QR code from the public URL so that users can easily monitor render status on any browser or mobile device.

- **Custom Logging:**  
  Implements a custom logging mechanism that aggregates messages from various parts of the render pipeline (asset loading, BVH generation, compositing, errors, etc.) into a log console.

![demo](https://github.com/user-attachments/assets/d0cde59c-d85b-47a6-83b5-1cf97935bfe9)

  

## Installation

1. **Download and Install the Addon:**
   - Clone this repository or download it as a ZIP.
   - In Blender, open **Edit > Preferences > Add-ons**.
   - Click **Install...** and select the downloaded ZIP file or the folder containing the addon.
   - Enable the addon by checking its box.

2. **Install Required Python Modules:**
   - Ensure that Blender’s Python environment has the required modules installed:
     ```bash
     pip install miniupnpc qrcode
     ```
   - Alternatively, click the **Activate (Install Dependencies)** button in the addon’s UI panel to install these automatically.

## Usage

1. **Start the Server:**
   - In the 3D View sidebar under the **Render Status** tab, click **Start Server**.
   - The addon will automatically:
     - Map your NAT via UPnP.
     - Create an IPv6/dual‑stack socket.
     - Add the necessary firewall rules (if required on your OS).
     - Generate a unique public URL and QR code.

2. **Monitor Your Render:**
   - Open the generated URL in any web browser (or scan the QR code with your mobile device).
   - The webpage will display:
     - A progress bar indicating render progress.
     - Live render statistics (current frame, total frames, last frame time, total expected time, etc.).
     - A log console showing detailed messages from the render pipeline.

3. **Stop the Server:**
   - Once finished, click **Stop Server** in the addon’s UI panel to shut down the HTTP server and remove any firewall/NAT mappings.

## FAQ

**Q: Do I need to configure AWS or any external services?**  
A: No. Initially, an AWS-based solution was explored. However, we transitioned to using IPv6 and dual‑stack NAT mapping for a zero‑user setup, eliminating manual configuration and external dependencies.

**Q: Which Blender versions are supported?**  
A: The addon works on lower Blender versions, but Blender 4.3+ is recommended for the best experience and full feature support.

**Q: What if my firewall blocks the port?**  
A: The addon attempts to add a firewall rule automatically on Windows and Linux. On macOS, you may need to manually allow incoming connections on port 8080.

**Q: How does the addon capture and display render logs?**  
A: A custom logging mechanism (built using Python’s logging module) aggregates log messages from different parts of the render pipeline (such as asset loading, BVH generation, compositing, and errors) and displays them in a log console on the web UI.

**Q: Who is responsible for issues with this addon?**  
A: This addon is an independent project and is not affiliated with the Blender Foundation. Any issues or errors are solely the responsibility of the addon.



https://github.com/user-attachments/assets/0d52afff-f44f-484a-b0c4-2baa8ee4b501



## Contributing

Contributions, bug reports, and feature requests are welcome. Please open an issue or submit a pull request with your changes. When contributing, ensure that your modifications are well documented and follow the project’s coding style.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
