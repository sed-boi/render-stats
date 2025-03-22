bl_info = {
    "name": "Render-Stats",
    "author": "Vishal Chaudhary",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Render Status",
    "description": ("Starts an HTTP server that maps your NAT via UPnP and supports IPv6/dual‑stack "
                    "connections. The server provides a browser-friendly UI to monitor live render status. "
                    "Render statistics update dynamically via render handlers."),
    "warning": "",
    "category": "Render",
}

import bpy
from .main import register as main_register, unregister as main_unregister
from .stats import update_render_stats_handler, clear_render_log

def register_render_handlers():
    # Register the render_post handler to update stats after each frame.
    if update_render_stats_handler not in bpy.app.handlers.render_post:
        bpy.app.handlers.render_post.append(update_render_stats_handler)
        print("Render post handler registered.")
    # Register render_init handler to clear log at the start.
    if clear_render_log not in bpy.app.handlers.render_init:
        bpy.app.handlers.render_init.append(clear_render_log)
        print("Render init handler registered.")

def unregister_render_handlers():
    if update_render_stats_handler in bpy.app.handlers.render_post:
        bpy.app.handlers.render_post.remove(update_render_stats_handler)
        print("Render post handler unregistered.")
    if clear_render_log in bpy.app.handlers.render_init:
        bpy.app.handlers.render_init.remove(clear_render_log)
        print("Render init handler unregistered.")

def register():
    register_render_handlers()
    main_register()
    print("Render Stats Addon registered.")

def unregister():
    main_unregister()
    unregister_render_handlers()
    print("Render Stats Addon unregistered.")

if __name__ == "__main__":
    register()
