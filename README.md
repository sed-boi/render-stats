# Render Stats Addon

This Blender addon creates a lightweight HTTP server that maps your NAT via UPnP and supports IPv6/dual‑stack connections. It serves a browser-friendly UI that displays live render statistics (current frame, total frames, progress, last frame time, etc.) along with a progress bar and a log console that aggregates messages from your render pipeline.

## Features

- **Dynamic Render Statistics:**  
  Uses Blender’s render post handler to update live data after every rendered frame.

- **Browser-friendly UI:**  
  Serves an HTML page with a progress bar, log console, and updated render stats that refresh every second.

- **NAT Mapping & Dual‑Stack Support:**  
  Utilizes UPnP (via miniupnpc) to set up real port mappings and creates an IPv6 socket (dual‑stack if available).

- **Automatic QR Code Generation:**  
  Generates a QR code from the public URL so that users can easily monitor render status on any browser.

- **Custom Logging:**  
  Implements a custom logger that aggregates log messages from various parts of the render pipeline.

## Installation

1. Install the required Python modules (miniupnpc and qrcode) in Blender’s Python environment. For example:
   ```bash
   pip install miniupnpc qrcode
