# Author: Aman Rathore
# Contact: amanr.me | amanrathore9753 <at> gmail <dot> com
# Created on: Friday, July 18, 2025 at 10:47

"""
Python Version: 3.13.5 | packaged by Anaconda, Inc. | (main, Jun 12 2025, 16:37:03) [MSC v.1929 64 bit (AMD64)]
OpenCV Version: 4.12.0
"""

import sys
import cv2
import json
import os
from pathlib import Path
from colored import fg, bg, attr
from tqdm import tqdm
import time
import numpy as np
import colorsys

# Beautiful terminal output setup
def print_header():
    """Print a beautiful header"""
    print(f"\n{fg('cyan')}{attr('bold')}{'='*60}{attr('reset')}")
    print(f"{fg('magenta')}{attr('bold')}🐭 MICE MOBILITY ANALYSER 🐭{attr('reset')}")
    print(f"{fg('cyan')}{attr('bold')}{'='*60}{attr('reset')}\n")

def print_info(message, icon="ℹ️"):
    """Print info message with styling"""
    print(f"{fg('blue')}{icon} {message}{attr('reset')}")

def print_success(message, icon="✅"):
    """Print success message with styling"""
    print(f"{fg('green')}{icon} {message}{attr('reset')}")

def print_warning(message, icon="⚠️"):
    """Print warning message with styling"""
    print(f"{fg('yellow')}{icon} {message}{attr('reset')}")

def print_error(message, icon="❌"):
    """Print error message with styling"""
    print(f"{fg('red')}{icon} {message}{attr('reset')}")

def print_section(title):
    """Print section header"""
    print(f"\n{fg('cyan')}{attr('bold')}{title}{attr('reset')}")
    print(f"{fg('cyan')}{'-' * len(title)}{attr('reset')}")

def generate_colors(num_colors):
    """Generate distinct colors using HSV color space"""
    colors = []
    for i in range(num_colors):
        hue = i / num_colors
        saturation = 0.8 + (i % 2) * 0.2  # Alternate between 0.8 and 1.0
        value = 0.9 + (i % 3) * 0.1       # Cycle through 0.9, 1.0, 1.1 (clamped)
        
        # Convert HSV to RGB
        rgb = colorsys.hsv_to_rgb(hue, saturation, min(value, 1.0))
        # Convert to BGR for OpenCV (0-255 range)
        bgr = [int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255)]
        colors.append(bgr)
    
    return colors

def get_rotated_rectangle_points(top_left, bottom_right, rotation_degrees):
    """Get the four corner points of a rotated rectangle"""
    x1, y1 = top_left
    x2, y2 = bottom_right
    
    # Center of the rectangle
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # Convert rotation to radians
    rotation_rad = np.radians(rotation_degrees)
    
    # Original corners relative to center
    corners = np.array([
        [x1 - center_x, y1 - center_y],  # Top-left
        [x2 - center_x, y1 - center_y],  # Top-right
        [x2 - center_x, y2 - center_y],  # Bottom-right
        [x1 - center_x, y2 - center_y]   # Bottom-left
    ])
    
    # Rotation matrix
    cos_rot = np.cos(rotation_rad)
    sin_rot = np.sin(rotation_rad)
    rotation_matrix = np.array([
        [cos_rot, -sin_rot],
        [sin_rot, cos_rot]
    ])
    
    # Apply rotation
    rotated_corners = np.dot(corners, rotation_matrix.T)
    
    # Translate back to original position
    rotated_corners[:, 0] += center_x
    rotated_corners[:, 1] += center_y
    
    return rotated_corners.astype(np.int32)

def draw_frame_overlays(image, frames_config):
    """Draw frame overlays on the image"""
    overlay = image.copy()
    
    for i, frame_config in enumerate(frames_config):
        top_left = frame_config['top_left']
        bottom_right = frame_config['bottom_right']
        rotation = frame_config.get('rotation', 0)
        color = frame_config.get('color')
        name = frame_config.get('name', f'Frame_{i+1}')
        
        # Get rotated rectangle points
        points = get_rotated_rectangle_points(top_left, bottom_right, rotation)
        
        # Draw the rotated rectangle
        cv2.polylines(overlay, [points], True, color, 3)
        
        # Fill with semi-transparent color
        cv2.fillPoly(overlay, [points], color)
        
        # Add frame label
        label_pos = (int(np.mean(points[:, 0])), int(np.mean(points[:, 1])))
        cv2.putText(overlay, name, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(overlay, name, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    
    # Blend with original image
    result = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
    return result

# Initialize with beautiful output
print_header()
print_info(f"Python Version: {sys.version.split()[0]}")
print_info(f"OpenCV Version: {cv2.__version__}")

def load_config(config_path="config.json"):
    """Load configuration from JSON file"""
    print_section("🔧 Loading Configuration")
    
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
        
        # Process frames configuration
        if 'frames' in config:
            frames = config['frames']
            colors_needed = []
            
            # Count frames that need auto-generated colors
            for frame in frames:
                if frame.get('color') is None:
                    colors_needed.append(frame)
            
            # Generate colors for frames that don't have them
            if colors_needed:
                auto_colors = generate_colors(len(colors_needed))
                color_index = 0
                
                for frame in frames:
                    if frame.get('color') is None:
                        frame['color'] = auto_colors[color_index]
                        color_index += 1
        
        print_success(f"Configuration loaded from '{config_path}'")
        return config
    except FileNotFoundError:
        print_error(f"Config file '{config_path}' not found!")
        return None
    except json.JSONDecodeError:
        print_error(f"Error parsing config file '{config_path}'!")
        return None

def play_video(video_path, window_width=800, window_height=600, show_fps=True, draw_frames=False, frames_config=None):
    """Play video using OpenCV with frame overlay option"""
    
    print_section("📹 Video Player")
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print_error(f"Video file not found: {video_path}")
        return False
    
    # Create video capture object
    print_info("Initializing video capture...")
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print_error(f"Could not open video file {video_path}")
        return False
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Display video information with beautiful formatting
    print_success(f"Video loaded: {fg('yellow')}{Path(video_path).name}{attr('reset')}")
    print_info(f"📊 Total frames: {fg('yellow')}{total_frames:,}{attr('reset')}")
    print_info(f"⚡ FPS: {fg('yellow')}{fps:.2f}{attr('reset')}")
    print_info(f"⏱️  Duration: {fg('yellow')}{duration:.2f} seconds{attr('reset')}")
    print_info(f"📐 Resolution: {fg('yellow')}{width}x{height}{attr('reset')}")
    
    if draw_frames and frames_config:
        print_info(f"🎨 Frame overlay: {fg('yellow')}Enabled ({len(frames_config)} frames){attr('reset')}")
        for i, frame_config in enumerate(frames_config):
            name = frame_config.get('name', f'Frame_{i+1}')
            color = frame_config['color']
            top_left = frame_config['top_left']
            bottom_right = frame_config['bottom_right']
            rotation = frame_config.get('rotation', 0)
            
            color_rgb = f"BGR({color[0]},{color[1]},{color[2]})"
            print_info(f"   {name}: {fg('yellow')}{color_rgb}{attr('reset')} | Position: {top_left} → {bottom_right} | Rotation: {rotation}°")
    
    # Show controls with beautiful formatting
    print_section("🎮 Controls")
    controls = [
        ("🚪", "Press 'q' to quit"),
        ("⏯️", "Press 'p' to pause/resume"),
        ("👆", "Press 's' to step frame by frame (when paused)"),
        ("🔄", "Press 'r' to restart video"),
        ("🎨", "Press 'f' to toggle frame overlays")
    ]
    
    for icon, control in controls:
        print(f"  {icon} {fg('green')}{control}{attr('reset')}")
    
    print()
    
    # Create window
    cv2.namedWindow('Mice Mobility Analyser - Video Player', cv2.WINDOW_NORMAL)
    
    paused = False
    frame_count = 0
    show_overlays = draw_frames
    
    # Progress bar setup
    pbar = tqdm(total=total_frames, desc="Playing video", 
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                colour='green')
    
    print_info("🎬 Starting video playback...")
    
    while True:
        if not paused:
            ret, frame = cap.read()
            
            if not ret:
                print_success("🎬 End of video reached")
                break
            
            frame_count += 1
            pbar.update(1)
        
        # Create display frame
        display_frame = frame.copy()
        
        # Resize frame if specified
        if window_width and window_height:
            # Calculate scaling factors
            scale_x = window_width / width
            scale_y = window_height / height
            
            display_frame = cv2.resize(display_frame, (window_width, window_height))
            
            # Scale frame configurations for display
            if show_overlays and frames_config:
                scaled_frames_config = []
                for frame_config in frames_config:
                    scaled_config = frame_config.copy()
                    scaled_config['top_left'] = [int(frame_config['top_left'][0] * scale_x), 
                                               int(frame_config['top_left'][1] * scale_y)]
                    scaled_config['bottom_right'] = [int(frame_config['bottom_right'][0] * scale_x), 
                                                   int(frame_config['bottom_right'][1] * scale_y)]
                    scaled_frames_config.append(scaled_config)
                
                display_frame = draw_frame_overlays(display_frame, scaled_frames_config)
        else:
            # Use original frame configurations
            if show_overlays and frames_config:
                display_frame = draw_frame_overlays(display_frame, frames_config)
        
        # Get frame dimensions for text positioning
        frame_height, frame_width = display_frame.shape[:2]
        
        # Add FPS and frame info overlay at bottom left
        if show_fps:
            current_time = frame_count / fps if fps > 0 else 0
            info_lines = [
                f"Frame: {frame_count}/{total_frames}",
                f"Time: {current_time:.2f}s",
                f"FPS: {fps:.1f}"
            ]
            
            # Add frame overlay info if enabled
            if show_overlays and frames_config:
                info_lines.append(f"Overlays: {len(frames_config)} frames")
            
            # Position text at bottom left
            line_height = 25
            start_y = frame_height - (len(info_lines) * line_height) - 10
            
            for i, line in enumerate(info_lines):
                y_pos = start_y + (i * line_height)
                # Add background rectangle for better readability
                text_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(display_frame, (5, y_pos - 20), (text_size[0] + 15, y_pos + 5), (0, 0, 0), -1)
                cv2.putText(display_frame, line, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            if paused:
                # Center the PAUSED text
                paused_text = "PAUSED"
                text_size = cv2.getTextSize(paused_text, cv2.FONT_HERSHEY_SIMPLEX, 2, 3)[0]
                x_pos = (frame_width - text_size[0]) // 2
                y_pos = frame_height // 2
                cv2.rectangle(display_frame, (x_pos - 10, y_pos - 40), (x_pos + text_size[0] + 10, y_pos + 10), (0, 0, 0), -1)
                cv2.putText(display_frame, paused_text, (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
        
        # Display frame
        cv2.imshow('Mice Mobility Analyser - Video Player', display_frame)
        
        # Handle keyboard input
        key = cv2.waitKey(1 if not paused else 0) & 0xFF
        
        if key == ord('q'):
            print_info("🚪 User quit video player")
            break
        elif key == ord('p'):
            paused = not paused
            status = "⏸️  Paused" if paused else "▶️  Resumed"
            print_info(status)
            if paused:
                pbar.set_description("Video paused")
            else:
                pbar.set_description("Playing video")
        elif key == ord('s') and paused:
            ret, frame = cap.read()
            if ret:
                frame_count += 1
                pbar.update(1)
                print_info(f"👆 Stepped to frame {frame_count}")
        elif key == ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            frame_count = 0
            pbar.reset()
            paused = False
            print_info("🔄 Video restarted")
        elif key == ord('f'):
            show_overlays = not show_overlays
            status = "🎨 Frame overlays enabled" if show_overlays else "🎨 Frame overlays disabled"
            print_info(status)
    
    # Clean up
    pbar.close()
    cap.release()
    cv2.destroyAllWindows()
    print_success("🧹 Video player cleaned up successfully")
    return True

def main():
    """Main function"""
    # Load configuration
    config = load_config()
    
    if config is None:
        print_warning("Using default configuration...")
        config = {
            "video_path": "sample_video.mp4",
            "window_width": 800,
            "window_height": 600,
            "fps_display": True,
            "draw_frames": False,
            "frames": []
        }
    
    # Get video path from config
    video_path = config.get("video_path", "")
    
    if not video_path:
        print_error("No video path specified in config!")
        return
    
    # Get other settings
    window_width = config.get("window_width", 800)
    window_height = config.get("window_height", 600)
    fps_display = config.get("fps_display", True)
    draw_frames = config.get("draw_frames", False)
    frames_config = config.get("frames", [])
    
    # Display configuration with beautiful formatting
    print_section("⚙️  Configuration")
    print_info(f"📁 Video path: {fg('yellow')}{video_path}{attr('reset')}")
    print_info(f"📏 Window size: {fg('yellow')}{window_width}x{window_height}{attr('reset')}")
    print_info(f"📊 FPS display: {fg('yellow')}{fps_display}{attr('reset')}")
    print_info(f"🎨 Frame overlay: {fg('yellow')}{draw_frames}{attr('reset')}")
    if draw_frames and frames_config:
        print_info(f"🔢 Number of frames: {fg('yellow')}{len(frames_config)}{attr('reset')}")
    
    # Add a small delay for better UX
    print_info("🚀 Initializing video player...")
    time.sleep(1)
    
    # Play video
    success = play_video(video_path, window_width, window_height, fps_display, draw_frames, frames_config)
    
    if not success:
        print_error("Failed to play video!")
    else:
        print_success("Video playback completed successfully!")
    
    print(f"\n{fg('cyan')}{attr('bold')}Thank you for using Mice Mobility Analyser! 🐭{attr('reset')}\n")

if __name__ == "__main__":
    main()

