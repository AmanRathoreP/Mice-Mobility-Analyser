# Author: Aman Rathore
# Contact: amanr.me | amanrathore9753 <at> gmail <dot> com
# Created on: Monday, July 21, 2025 at 14:55

import customtkinter as ctk
import cv2
import json
import numpy as np
from PIL import Image, ImageTk
import colorsys
from pathlib import Path
import tkinter.messagebox as messagebox
import random
import tkinter as tk

class FrameEditorGUI:
    def __init__(self):
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize main window
        self.root = ctk.CTk()
        self.root.title("🐭 Mice Mobility Analyser - Frame Editor")
        self.root.geometry("1600x1000")
        
        # Load configuration
        self.config = self.load_config()
        if not self.config:
            messagebox.showerror("Error", "Could not load config.json!")
            self.root.destroy()
            return
        
        # Initialize video
        self.video_cap = None
        self.current_frame = None
        self.original_frame = None
        self.frame_count = 0
        self.total_frames = 0
        
        # Frame data
        self.frames_data = self.config.get("frames", [])
        self.selected_frame_index = 0
        
        # Zoom and pan variables
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.is_panning = False
        
        # Initialize video capture
        self.init_video()
        
        # Create GUI
        self.create_gui()
        
        # Load first frame
        self.load_random_frame()
        
        # Update display
        self.update_frame_display()
        self.update_frame_controls()
    
    def load_config(self, config_path="config.json"):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as file:
                config = json.load(file)
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return None
    
    def save_config(self, config_path="config.json"):
        """Save configuration to JSON file"""
        try:
            # Update config with current frames data
            self.config["frames"] = self.frames_data
            
            with open(config_path, 'w') as file:
                json.dump(self.config, file, indent=4)
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
            return False
    
    def init_video(self):
        """Initialize video capture"""
        video_path = self.config.get("video_path", "")
        if not video_path or not Path(video_path).exists():
            messagebox.showerror("Error", f"Video file not found: {video_path}")
            return False
        
        self.video_cap = cv2.VideoCapture(video_path)
        if not self.video_cap.isOpened():
            messagebox.showerror("Error", f"Could not open video file: {video_path}")
            return False
        
        self.total_frames = int(self.video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return True
    
    def generate_color_for_frame(self, index):
        """Generate a distinct color for a frame"""
        hue = (index * 0.618033988749895) % 1.0  # Golden ratio for better distribution
        saturation = 0.8
        value = 0.9
        
        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        bgr = [int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255)]
        return bgr
    
    def create_gui(self):
        """Create the main GUI layout"""
        # Main container
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="🐭 Frame Editor - Define Analysis Zones",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Create main content area
        content_frame = ctk.CTkFrame(self.main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Video display
        self.create_video_panel(content_frame)
        
        # Right panel - Controls
        self.create_control_panel(content_frame)
    
    def create_video_panel(self, parent):
        """Create video display panel"""
        self.video_frame = ctk.CTkFrame(parent)
        self.video_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Video display label
        video_title = ctk.CTkLabel(
            self.video_frame,
            text="📹 Video Preview",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        video_title.pack(pady=(10, 5))
        
        # Control buttons frame
        button_frame = ctk.CTkFrame(self.video_frame)
        button_frame.pack(pady=5)
        
        # Frame selection button
        self.frame_button = ctk.CTkButton(
            button_frame,
            text="🎲 Load Random Frame",
            command=self.load_random_frame,
            font=ctk.CTkFont(size=14)
        )
        self.frame_button.pack(side="left", padx=5)
        
        # Zoom controls
        zoom_in_button = ctk.CTkButton(
            button_frame,
            text="🔍+ Zoom In",
            command=self.zoom_in,
            font=ctk.CTkFont(size=12),
            width=100
        )
        zoom_in_button.pack(side="left", padx=2)
        
        zoom_out_button = ctk.CTkButton(
            button_frame,
            text="🔍- Zoom Out",
            command=self.zoom_out,
            font=ctk.CTkFont(size=12),
            width=100
        )
        zoom_out_button.pack(side="left", padx=2)
        
        reset_zoom_button = ctk.CTkButton(
            button_frame,
            text="🔄 Reset Zoom",
            command=self.reset_zoom,
            font=ctk.CTkFont(size=12),
            width=100
        )
        reset_zoom_button.pack(side="left", padx=2)
        
        # Zoom info label
        self.zoom_info_label = ctk.CTkLabel(
            self.video_frame,
            text="Zoom: 100% | Click and drag to pan",
            font=ctk.CTkFont(size=12)
        )
        self.zoom_info_label.pack(pady=2)
        
        # Create canvas for video display with scrollbars
        canvas_frame = ctk.CTkFrame(self.video_frame)
        canvas_frame.pack(fill="both", expand=True, pady=10)
        
        # Create canvas
        self.canvas = tk.Canvas(canvas_frame, bg='black')
        self.canvas.pack(fill="both", expand=True)
        
        # Bind mouse events for panning and zooming
        self.canvas.bind("<Button-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
    
    def on_mouse_press(self, event):
        """Handle mouse press for panning"""
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.is_panning = True
    
    def on_mouse_drag(self, event):
        """Handle mouse drag for panning"""
        if self.is_panning:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y
            self.pan_x += dx
            self.pan_y += dy
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self.update_frame_display()
    
    def on_mouse_release(self, event):
        """Handle mouse release"""
        self.is_panning = False
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def zoom_in(self):
        """Zoom in the image"""
        self.zoom_factor = min(self.zoom_factor * 1.2, 5.0)
        self.update_zoom_info()
        self.update_frame_display()
    
    def zoom_out(self):
        """Zoom out the image"""
        self.zoom_factor = max(self.zoom_factor / 1.2, 0.2)
        self.update_zoom_info()
        self.update_frame_display()
    
    def reset_zoom(self):
        """Reset zoom and pan"""
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.update_zoom_info()
        self.update_frame_display()
    
    def update_zoom_info(self):
        """Update zoom information display"""
        zoom_percent = int(self.zoom_factor * 100)
        self.zoom_info_label.configure(text=f"Zoom: {zoom_percent}% | Click and drag to pan")
    
    def create_control_panel(self, parent):
        """Create control panel"""
        self.control_frame = ctk.CTkFrame(parent)
        self.control_frame.pack(side="right", fill="y", padx=(10, 0))
        self.control_frame.configure(width=450)
        
        # Controls title
        controls_title = ctk.CTkLabel(
            self.control_frame,
            text="🎛️ Frame Controls",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        controls_title.pack(pady=(10, 20))
        
        # Frame list section
        self.create_frame_list_section()
        
        # Frame editor section
        self.create_frame_editor_section()
        
        # Action buttons
        self.create_action_buttons()
    
    def create_frame_list_section(self):
        """Create frame list section"""
        # Frame list title
        list_title = ctk.CTkLabel(
            self.control_frame,
            text="📋 Frame List",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        list_title.pack(pady=(0, 10))
        
        # Frame list
        self.frame_listbox = ctk.CTkScrollableFrame(self.control_frame, height=150)
        self.frame_listbox.pack(fill="x", padx=10, pady=(0, 10))
        
        # Buttons for frame management
        button_frame = ctk.CTkFrame(self.control_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 20))
        
        self.add_button = ctk.CTkButton(
            button_frame,
            text="➕ Add Frame",
            command=self.add_new_frame,
            width=100
        )
        self.add_button.pack(side="left", padx=(0, 5))
        
        self.delete_button = ctk.CTkButton(
            button_frame,
            text="🗑️ Delete",
            command=self.delete_frame,
            width=100,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_button.pack(side="right", padx=(5, 0))
    
    def create_frame_editor_section(self):
        """Create frame editor section"""
        # Editor title
        editor_title = ctk.CTkLabel(
            self.control_frame,
            text="✏️ Edit Selected Frame",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        editor_title.pack(pady=(0, 10))
        
        # Scrollable editor frame
        self.editor_frame = ctk.CTkScrollableFrame(self.control_frame, height=400)
        self.editor_frame.pack(fill="x", padx=10, pady=(0, 20))
        
        # Frame name
        self.create_name_control()
        
        # Position controls with text boxes
        self.create_position_controls()
        
        # Rotation control
        self.create_rotation_control()
    
    def create_name_control(self):
        """Create frame name control"""
        name_label = ctk.CTkLabel(self.editor_frame, text="📛 Frame Name:")
        name_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.name_entry = ctk.CTkEntry(
            self.editor_frame,
            placeholder_text="Enter frame name..."
        )
        self.name_entry.pack(fill="x", padx=10, pady=(0, 15))
        self.name_entry.bind("<KeyRelease>", self.on_name_change)
    
    def create_position_controls(self):
        """Create position control sliders with text boxes"""
        # Get video dimensions for max values
        if self.video_cap:
            width = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        else:
            width, height = 800, 600
        
        # Top-left X
        self.create_slider_textbox_control("📍 Top-Left X:", "top_left_x", 0, width, 50)
        
        # Top-left Y
        self.create_slider_textbox_control("📍 Top-Left Y:", "top_left_y", 0, height, 150)
        
        # Bottom-right X
        self.create_slider_textbox_control("📍 Bottom-Right X:", "bottom_right_x", 0, width, 270)
        
        # Bottom-right Y
        self.create_slider_textbox_control("📍 Bottom-Right Y:", "bottom_right_y", 0, height, 500)
    
    def create_rotation_control(self):
        """Create rotation control slider with text box"""
        self.create_slider_textbox_control("🔄 Rotation (degrees):", "rotation", -180, 180, 0)
    
    def create_slider_textbox_control(self, label_text, var_name, min_val, max_val, default_val):
        """Create a slider control with text box and label"""
        # Label
        label = ctk.CTkLabel(self.editor_frame, text=label_text)
        label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Control frame
        control_frame = ctk.CTkFrame(self.editor_frame)
        control_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Slider
        slider = ctk.CTkSlider(
            control_frame,
            from_=min_val,
            to=max_val,
            number_of_steps=max_val - min_val,
            command=lambda x, name=var_name: self.on_slider_change(name, x)
        )
        slider.pack(side="top", fill="x", padx=10, pady=(10, 5))
        slider.set(default_val)
        
        # Text box frame
        textbox_frame = ctk.CTkFrame(control_frame)
        textbox_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Value label
        value_label = ctk.CTkLabel(textbox_frame, text="Value:", width=50)
        value_label.pack(side="left", padx=(10, 5))
        
        # Text box for manual input
        textbox = ctk.CTkEntry(
            textbox_frame,
            width=80,
            placeholder_text=str(default_val)
        )
        textbox.pack(side="left", padx=(0, 5))
        textbox.insert(0, str(default_val))
        textbox.bind("<KeyRelease>", lambda e, name=var_name: self.on_textbox_change(name, e))
        textbox.bind("<FocusOut>", lambda e, name=var_name: self.on_textbox_change(name, e))
        
        # Range label
        range_label = ctk.CTkLabel(textbox_frame, text=f"({min_val}-{max_val})", width=80)
        range_label.pack(side="left", padx=(5, 10))
        
        # Store references
        setattr(self, f"{var_name}_slider", slider)
        setattr(self, f"{var_name}_textbox", textbox)
        setattr(self, f"{var_name}_min", min_val)
        setattr(self, f"{var_name}_max", max_val)
    
    def create_action_buttons(self):
        """Create action buttons"""
        # Save button
        self.save_button = ctk.CTkButton(
            self.control_frame,
            text="💾 Save Configuration",
            command=self.save_config,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.save_button.pack(fill="x", padx=10, pady=(0, 10))
        
        # Reset button
        self.reset_button = ctk.CTkButton(
            self.control_frame,
            text="🔄 Reset to Original",
            command=self.reset_to_original,
            font=ctk.CTkFont(size=14),
            fg_color="orange",
            hover_color="darkorange"
        )
        self.reset_button.pack(fill="x", padx=10, pady=(0, 20))
    
    def load_random_frame(self):
        """Load a random frame from the video"""
        if not self.video_cap:
            return
        
        # Generate random frame number
        random_frame = random.randint(0, self.total_frames - 1)
        
        # Set video position to random frame
        self.video_cap.set(cv2.CAP_PROP_POS_FRAMES, random_frame)
        
        # Read frame
        ret, frame = self.video_cap.read()
        if ret:
            self.original_frame = frame.copy()
            self.current_frame = frame.copy()
            self.frame_count = random_frame
            self.update_frame_display()
    
    def update_frame_display(self):
        """Update the video frame display with overlays and zoom"""
        if self.original_frame is None:
            return
        
        # Create display frame
        display_frame = self.original_frame.copy()
        
        # Draw all frames
        for i, frame_data in enumerate(self.frames_data):
            self.draw_frame_overlay(display_frame, frame_data, i == self.selected_frame_index)
        
        # Apply zoom
        if self.zoom_factor != 1.0:
            new_width = int(display_frame.shape[1] * self.zoom_factor)
            new_height = int(display_frame.shape[0] * self.zoom_factor)
            display_frame = cv2.resize(display_frame, (new_width, new_height))
        
        # Convert to PIL Image
        display_frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(display_frame_rgb)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(pil_image)
        
        # Clear canvas and add image with pan offset
        self.canvas.delete("all")
        self.canvas.create_image(self.pan_x, self.pan_y, anchor="nw", image=photo)
        self.canvas.image = photo  # Keep a reference
        
        # Update canvas scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def draw_frame_overlay(self, image, frame_data, is_selected=False):
        """Draw frame overlay on image"""
        top_left = frame_data['top_left']
        bottom_right = frame_data['bottom_right']
        rotation = frame_data.get('rotation', 0)
        color = frame_data.get('color', [255, 255, 255])
        name = frame_data.get('name', 'Unnamed')
        
        # Get rotated rectangle points
        points = self.get_rotated_rectangle_points(top_left, bottom_right, rotation)
        
        # Use different colors for selected/unselected
        if is_selected:
            line_color = [255, 255, 0]  # Yellow for selected
            thickness = 4
        else:
            line_color = color
            thickness = 2
        
        # Draw rectangle
        cv2.polylines(image, [points], True, line_color, thickness)
        
        # Fill with semi-transparent color
        overlay = image.copy()
        cv2.fillPoly(overlay, [points], color)
        cv2.addWeighted(overlay, 0.3, image, 0.7, 0, image)
        
        # Add label
        label_pos = (int(np.mean(points[:, 0])), int(np.mean(points[:, 1])))
        cv2.putText(image, name, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(image, name, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    
    def get_rotated_rectangle_points(self, top_left, bottom_right, rotation_degrees):
        """Get the four corner points of a rotated rectangle"""
        x1, y1 = top_left
        x2, y2 = bottom_right
        
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        rotation_rad = np.radians(rotation_degrees)
        
        corners = np.array([
            [x1 - center_x, y1 - center_y],
            [x2 - center_x, y1 - center_y],
            [x2 - center_x, y2 - center_y],
            [x1 - center_x, y2 - center_y]
        ])
        
        cos_rot = np.cos(rotation_rad)
        sin_rot = np.sin(rotation_rad)
        rotation_matrix = np.array([
            [cos_rot, -sin_rot],
            [sin_rot, cos_rot]
        ])
        
        rotated_corners = np.dot(corners, rotation_matrix.T)
        rotated_corners[:, 0] += center_x
        rotated_corners[:, 1] += center_y
        
        return rotated_corners.astype(np.int32)
    
    def update_frame_list(self):
        """Update the frame list display"""
        # Clear existing widgets
        for widget in self.frame_listbox.winfo_children():
            widget.destroy()
        
        # Add frame buttons
        for i, frame_data in enumerate(self.frames_data):
            name = frame_data.get('name', f'Frame_{i+1}')
            
            button = ctk.CTkButton(
                self.frame_listbox,
                text=f"{i+1}. {name}",
                command=lambda idx=i: self.select_frame(idx),
                fg_color="blue" if i == self.selected_frame_index else "gray"
            )
            button.pack(fill="x", pady=2)
    
    def select_frame(self, index):
        """Select a frame for editing"""
        if 0 <= index < len(self.frames_data):
            self.selected_frame_index = index
            self.update_frame_list()
            self.update_frame_controls()
            self.update_frame_display()
    
    def update_frame_controls(self):
        """Update frame control values"""
        if not self.frames_data or self.selected_frame_index >= len(self.frames_data):
            return
        
        frame_data = self.frames_data[self.selected_frame_index]
        
        # Update name
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, frame_data.get('name', ''))
        
        # Update sliders and textboxes
        self.update_control_value("top_left_x", frame_data['top_left'][0])
        self.update_control_value("top_left_y", frame_data['top_left'][1])
        self.update_control_value("bottom_right_x", frame_data['bottom_right'][0])
        self.update_control_value("bottom_right_y", frame_data['bottom_right'][1])
        self.update_control_value("rotation", frame_data.get('rotation', 0))
    
    def update_control_value(self, var_name, value):
        """Update both slider and textbox for a control"""
        slider = getattr(self, f"{var_name}_slider")
        textbox = getattr(self, f"{var_name}_textbox")
        
        slider.set(value)
        textbox.delete(0, "end")
        textbox.insert(0, str(value))
    
    def on_name_change(self, event=None):
        """Handle name change"""
        if self.frames_data and self.selected_frame_index < len(self.frames_data):
            self.frames_data[self.selected_frame_index]['name'] = self.name_entry.get()
            self.update_frame_list()
    
    def on_slider_change(self, var_name, value):
        """Handle slider value change"""
        if not self.frames_data or self.selected_frame_index >= len(self.frames_data):
            return
        
        int_value = int(value)
        
        # Update the textbox
        textbox = getattr(self, f"{var_name}_textbox")
        textbox.delete(0, "end")
        textbox.insert(0, str(int_value))
        
        # Update frame data
        self.update_frame_data(var_name, int_value)
    
    def on_textbox_change(self, var_name, event):
        """Handle textbox value change"""
        if not self.frames_data or self.selected_frame_index >= len(self.frames_data):
            return
        
        try:
            textbox = getattr(self, f"{var_name}_textbox")
            value = int(textbox.get())
            
            # Clamp value to valid range
            min_val = getattr(self, f"{var_name}_min")
            max_val = getattr(self, f"{var_name}_max")
            value = max(min_val, min(max_val, value))
            
            # Update textbox if value was clamped
            if int(textbox.get()) != value:
                textbox.delete(0, "end")
                textbox.insert(0, str(value))
            
            # Update slider
            slider = getattr(self, f"{var_name}_slider")
            slider.set(value)
            
            # Update frame data
            self.update_frame_data(var_name, value)
            
        except ValueError:
            # Invalid input, ignore
            pass
    
    def update_frame_data(self, var_name, value):
        """Update frame data and refresh display"""
        frame_data = self.frames_data[self.selected_frame_index]
        
        if var_name == "top_left_x":
            frame_data['top_left'][0] = value
        elif var_name == "top_left_y":
            frame_data['top_left'][1] = value
        elif var_name == "bottom_right_x":
            frame_data['bottom_right'][0] = value
        elif var_name == "bottom_right_y":
            frame_data['bottom_right'][1] = value
        elif var_name == "rotation":
            frame_data['rotation'] = value
        
        # Update display
        self.update_frame_display()
    
    def add_new_frame(self):
        """Add a new frame"""
        # Get video dimensions for default positioning
        if self.video_cap:
            width = int(self.video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            default_width = min(200, width // 4)
            default_height = min(200, height // 4)
        else:
            default_width = default_height = 200
        
        new_frame = {
            "name": f"Frame_{len(self.frames_data) + 1}",
            "top_left": [100, 100],
            "bottom_right": [100 + default_width, 100 + default_height],
            "rotation": 0,
            "color": self.generate_color_for_frame(len(self.frames_data))
        }
        
        self.frames_data.append(new_frame)
        self.selected_frame_index = len(self.frames_data) - 1
        
        self.update_frame_list()
        self.update_frame_controls()
        self.update_frame_display()
    
    def delete_frame(self):
        """Delete the selected frame"""
        if not self.frames_data:
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this frame?"):
            del self.frames_data[self.selected_frame_index]
            
            if self.selected_frame_index >= len(self.frames_data):
                self.selected_frame_index = max(0, len(self.frames_data) - 1)
            
            self.update_frame_list()
            if self.frames_data:
                self.update_frame_controls()
            self.update_frame_display()
    
    def reset_to_original(self):
        """Reset to original configuration"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset to the original configuration?"):
            self.config = self.load_config()
            self.frames_data = self.config.get("frames", [])
            self.selected_frame_index = 0
            
            self.update_frame_list()
            if self.frames_data:
                self.update_frame_controls()
            self.update_frame_display()
    
    def run(self):
        """Run the GUI"""
        self.update_frame_list()
        self.root.mainloop()
        
        # Clean up
        if self.video_cap:
            self.video_cap.release()

def main():
    """Main function to run the Frame Editor GUI"""
    app = FrameEditorGUI()
    app.run()

if __name__ == "__main__":
    main()