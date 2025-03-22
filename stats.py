# stats.py
import logging

# Global variable to store the most recent render statistics.
current_render_stats = {}

# Global log string that accumulates log messages.
render_log = ""

# Custom logging handler that appends log messages to render_log.
class LogHandler(logging.Handler):
    def emit(self, record):
        global render_log
        msg = self.format(record)
        render_log += msg + "\n"
        # Optionally, also print to console for debugging.
        print(msg)

# Set up our custom logger.
logger = logging.getLogger("RenderStatsLogger")
logger.setLevel(logging.DEBUG)
# Clear any existing handlers.
logger.handlers = []
handler = LogHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def update_render_stats_handler(scene):
    """
    This handler is called after each rendered frame (via render_post).
    It updates the global statistics dictionary with the current frame,
    total frames, estimated times, and accumulates the current log.
    """
    global current_render_stats, render_log
    current_frame = scene.frame_current
    total_frames = scene.frame_end
    last_frame_time = 0.033  # Replace with a dynamic measurement if available.
    total_expected_time = (total_frames - current_frame) * last_frame_time
    render_active = True  # You can refine this based on the actual render state.

    progress_percentage = (current_frame / total_frames * 100) if total_frames > 0 else 0

    stats = {
        "current_frame": current_frame,
        "total_frames": total_frames,
        "progress_percentage": progress_percentage,
        "last_frame_time": last_frame_time,
        "total_expected_time": total_expected_time,
        "render_active": render_active,
        # System performance fields removed.
        "log": render_log,
    }
    current_render_stats = stats.copy()
    logger.info(f"Frame {current_frame} rendered. Progress: {progress_percentage:.2f}%")

def clear_render_log(scene):
    """
    Clear the global render log when a new render is starting.
    This handler is registered with render_init.
    """
    global render_log
    render_log = ""
    logger.info("Render log cleared at render initialization.")

def get_render_stats():
    """
    Returns the current render statistics.
    If not available, returns default values.
    """
    global current_render_stats
    if not current_render_stats:
        return {
            "current_frame": 0,
            "total_frames": 0,
            "progress_percentage": 0,
            "last_frame_time": 0,
            "total_expected_time": 0,
            "render_active": False,
            "log": "",
        }
    return current_render_stats
