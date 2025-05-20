#!/usr/bin/env python3
"""
Tello XR Video Stream Module - Enhanced with optimized H.264 decoding
Video stream processor for Tello drone with improved frame handling and error recovery
"""
import time

import cv2

# Tello video stream address constant
TELLO_VIDEO_STREAM_ADDRESS = "udp://0.0.0.0:11111"

# Display English-only notification
print("INFO: Using enhanced video stream with optimized H.264 decoding")


class VideoStream:
    """Class to handle video streaming from Tello drone with improved H.264 decoding"""

    def __init__(self):
        """Initialize the VideoStream class with optimized settings"""
        self.cap = None
        self.frame_count = 0
        self.start_time = time.time()
        self.fps = 0
        self.show_info = True  # UI information display flag
        self.last_frame_time = time.time()  # Frame acquisition time measurement
        self.dropped_frames = 0  # Dropped frame counter
        self.total_frames = 0  # Total frame counter
        self.connection_status = "Not Connected"  # Connection status
        self.last_successful_frame = None  # Store the last successful frame for stability
        self.decode_errors = 0  # Counter for H.264 decode errors
        self.prev_decode_check_time = time.time()  # Time of the last decode error check

    def connect(self, retry_limit=5):
        """
        Connect to the video stream with improved H.264 decoding settings

        Parameters:
            retry_limit (int): Maximum number of connection attempts

        Returns:
            bool: True if connection succeeds, False otherwise
        """
        retry_count = 0

        while self.cap is None and retry_count < retry_limit:
            try:
                print(f"Attempting to connect to video stream ({retry_count+1}/{retry_limit})...")

                # Set advanced options for FFmpeg to improve H.264 decoding
                # Use FFMPEG backend explicitly with hardware acceleration if available
                if cv2.ocl.useOpenCL():
                    print("OpenCL acceleration is available and enabled")
                    cv2.setUseOptimized(True)

                # Create FFmpeg command with optimizations for UDP stream
                ffmpeg_options = {
                    "rtsp_transport": "udp",
                    "fflags": "nobuffer",  # Reduce latency
                    "flags": "low_delay",  # Prioritize low latency
                    "framedrop": "true",  # Allow frame drops to maintain sync
                    "strict": "experimental",  # Enable experimental features
                    "probesize": "32",  # Small probe size for faster start
                    "analyzeduration": "0",  # Minimal analyze time
                    "scan_all_pmts": "true",  # Scan all program map tables
                }

                # Build the FFmpeg command string from options
                ffmpeg_cmd = " ".join([f"{k}={v}" for k, v in ffmpeg_options.items()])

                # Initialize capture with FFmpeg options
                self.cap = cv2.VideoCapture(
                    TELLO_VIDEO_STREAM_ADDRESS + "?" + ffmpeg_cmd, cv2.CAP_FFMPEG
                )

                # Further optimizations for video capture
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Smaller buffer for reduced latency
                self.cap.set(cv2.CAP_PROP_FPS, 30)  # Target 30 FPS

                # Check if connection was successful
                if not self.cap.isOpened():
                    print(f"Failed to open camera (attempt {retry_count+1}/{retry_limit})")
                    time.sleep(1.5)
                    retry_count += 1
                    self.cap = None
                    continue

                # Initialize the decoder with dummy reads
                print("Initializing video decoder...")
                for _ in range(5):
                    self.cap.read()
                    time.sleep(0.1)

                print("Camera connected successfully!")
                self.connection_status = "Connected"
                self.decode_errors = 0
                return True

            except Exception as e:
                print(f"Camera connection error: {e} (attempt {retry_count+1}/{retry_limit})")
                if self.cap:
                    self.cap.release()
                    self.cap = None
                time.sleep(1.5)
                retry_count += 1

        print("Failed to connect to video stream")
        self.connection_status = "Not Connected"
        return False

    def read_frame(self):
        """
        Read one frame with improved error handling and frame stability

        Returns:
            tuple: (success flag, frame image)
        """
        if self.cap is None or not self.cap.isOpened():
            self.connection_status = "Disconnected"
            return False, None

        # Record frame timing for performance measurement
        now = time.time()
        frame_interval = now - self.last_frame_time

        # Check if we're having frequent decode errors
        if now - self.prev_decode_check_time > 5.0:  # Check every 5 seconds
            if self.decode_errors > 50:  # Too many decode errors
                print(
                    f"WARNING: High H.264 decode error rate detected ({self.decode_errors} in 5s). "
                    f"Reinitializing decoder..."
                )
                self.cap.release()
                self.cap = None
                self.connect(retry_limit=2)  # Try to reconnect with limited retries
                self.decode_errors = 0
            self.prev_decode_check_time = now

        # Attempt to read a frame with timeout
        try:
            if self.cap is None:
                return False, None

            ret, frame = self.cap.read()
            # Update timing information
            self.last_frame_time = time.time()

            if ret and frame is not None and frame.size > 0:
                self.frame_count += 1
                self.total_frames += 1
                self.connection_status = "Connected"
                self.last_successful_frame = frame.copy()  # Store successful frame

                # If frame interval is too long, it may indicate a frame drop
                if frame_interval > 0.1:  # More than 100ms between frames
                    self.dropped_frames += 1

                return ret, frame
            else:
                # Frame acquisition failed, increment error counters
                self.dropped_frames += 1
                self.decode_errors += 1
                self.connection_status = "Frame Error"

                # Return the last successful frame if we have one to maintain UI continuity
                if self.last_successful_frame is not None:
                    return True, self.last_successful_frame

                return False, None

        except Exception as e:
            print(f"Error reading frame: {e}")
            self.dropped_frames += 1
            self.decode_errors += 1
            self.connection_status = "Read Error"
            return False, None

    def calculate_fps(self, interval=30):
        """
        Calculate FPS (updated every 'interval' frames)

        Parameters:
            interval (int): Number of frames between FPS calculations

        Returns:
            float: Current FPS value
        """
        if self.frame_count % interval == 0 and self.frame_count > 0:
            current_time = time.time()
            elapsed = current_time - self.start_time
            if elapsed > 0:
                self.fps = interval / elapsed
                self.start_time = current_time

        return self.fps

    def display_frame(self, frame, window_name="Tello Video Stream"):
        """
        Display frame in window

        Parameters:
            frame: Frame image to display
            window_name (str): Name of display window

        Returns:
            int: Key input value (27 for ESC, 113 for 'q')
        """
        cv2.imshow(window_name, frame)
        return cv2.waitKey(1)

    def add_text_to_frame(
        self,
        frame,
        text,
        position,
        font_scale=0.7,
        color=(255, 255, 255),
        thickness=2,
        bg_color=None,
    ):
        """
        Add text overlay to a frame (English only)

        Parameters:
            frame: Target frame to add text to
            text (str): Text to display
            position (tuple): Text position (x, y)
            font_scale (float): Font size
            color (tuple): Text color (B, G, R)
            thickness (int): Text thickness
            bg_color (tuple): Background color (B, G, R), None for no background

        Returns:
            Frame with text added
        """
        # テキストに日本語が含まれる場合は英語に置換
        text = "".join(char if ord(char) < 128 else "?" for char in text)

        # 標準的なOpenCVテキスト描画を使用
        font = cv2.FONT_HERSHEY_SIMPLEX

        # テキストのサイズを取得
        if bg_color is not None:
            text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
            text_w, text_h = text_size

            # テキストの背景を描画
            cv2.rectangle(
                frame,
                (position[0], position[1] - text_h - 5),
                (position[0] + text_w, position[1] + 5),
                bg_color,
                -1,
            )

        # テキストを描画
        cv2.putText(frame, text, position, font, font_scale, color, thickness, cv2.LINE_AA)
        return frame

    def draw_controller_state(
        self, frame, controller_input, is_flying=False, battery=None, drone_state=None
    ):
        """
        Draw controller input state and drone status

        Parameters:
            frame: Frame to draw on
            controller_input (dict): Controller input state
            is_flying (bool): Whether drone is flying
            battery (int): Battery level (%), None if not available
            drone_state (dict): Additional drone state information

        Returns:
            Frame with UI added
        """
        if not self.show_info:
            # If UI display is off, return the original frame
            return frame

        h, w = frame.shape[:2]

        # Display flight status
        status_text = "Status: Flying" if is_flying else "Status: Landed"
        status_color = (0, 255, 0) if is_flying else (0, 165, 255)  # Green or orange
        self.add_text_to_frame(frame, status_text, (10, 30), 0.7, status_color, 2, (0, 0, 0, 128))

        # Display FPS and streaming status
        if self.fps > 0:
            fps_text = f"FPS: {self.fps:.1f} | {self.connection_status}"
            fps_color = (255, 255, 255)
            if self.connection_status != "Connected":
                fps_color = (0, 0, 255)  # Red for connection issues
            self.add_text_to_frame(frame, fps_text, (10, 60), 0.7, fps_color, 2, (0, 0, 0, 128))

        # Display battery level
        if battery is not None:
            battery_text = f"Battery: {battery}%"
            battery_color = (255, 255, 255)
            if battery <= 15:  # Red if battery below 15%
                battery_color = (0, 0, 255)
            elif battery <= 30:  # Orange if battery below 30%
                battery_color = (0, 165, 255)
            self.add_text_to_frame(
                frame, battery_text, (10, 90), 0.7, battery_color, 2, (0, 0, 0, 128)
            )

        # Display frame statistics (debug info)
        debug_text = f"Total frames: {self.total_frames} | Dropped: {self.dropped_frames}"
        self.add_text_to_frame(
            frame, debug_text, (w - 300, 30), 0.6, (150, 150, 150), 2, (0, 0, 0, 128)
        )

        # Display controller input values (if available)
        if controller_input and "movement" in controller_input:
            m = controller_input["movement"]

            # Show stick input values as text
            move_text = f"Move: X={m['x']:.2f} Y={m['y']:.2f} Z={m['z']:.2f} R={m['rotation']:.2f}"
            self.add_text_to_frame(
                frame, move_text, (10, h - 30), 0.6, (255, 255, 255), 2, (0, 0, 0, 128)
            )

            # Display stick input visually (crosshair)
            center_x, center_y = w - 80, h - 80
            radius = 50

            # Draw background circle
            cv2.circle(frame, (center_x, center_y), radius, (0, 0, 0, 128), -1)
            cv2.circle(frame, (center_x, center_y), radius, (100, 100, 100), 1)

            # X and Y axis lines
            cv2.line(
                frame, (center_x - radius, center_y), (center_x + radius, center_y), (70, 70, 70), 1
            )
            cv2.line(
                frame, (center_x, center_y - radius), (center_x, center_y + radius), (70, 70, 70), 1
            )

            # Show current stick position
            stick_x = int(center_x + m["x"] * radius)
            stick_y = int(center_y + m["y"] * radius)
            cv2.circle(frame, (stick_x, stick_y), 5, (0, 255, 0), -1)

        # ボタン状態を表示
        if "buttons" in controller_input:
            b = controller_input["buttons"]
            buttons_text = ""
            if b.get("takeoff", False):
                buttons_text += "Takeoff "
            if b.get("land", False):
                buttons_text += "Land "
            if b.get("emergency", False):
                buttons_text += "Emergency "
            if b.get("photo", False):
                buttons_text += "Photo "

            if buttons_text:
                self.add_text_to_frame(
                    frame, buttons_text, (10, h - 60), 0.6, (0, 255, 255), 2, (0, 0, 0, 128)
                )

        return frame

    def display_telemetry_data(self, frame, telemetry_data):
        """
        Display drone telemetry data on frame

        Parameters:
            frame: Target frame to draw on
            telemetry_data (dict): Dictionary of telemetry data

        Returns:
            Frame with telemetry data displayed
        """
        if not self.show_info or telemetry_data is None:
            return frame

        h, w = frame.shape[:2]

        # Create semi-transparent overlay (for telemetry panel)
        overlay = frame.copy()
        panel_width = 250  # Expanded panel width
        panel_height = 200  # Expanded panel height
        panel_x = w - panel_width - 10
        panel_y = 10

        # Panel background
        cv2.rectangle(
            overlay,
            (panel_x, panel_y),
            (panel_x + panel_width, panel_y + panel_height),
            (0, 0, 0),
            -1,
        )

        # Display telemetry data
        y_offset = panel_y + 20
        self.add_text_to_frame(
            overlay, "Telemetry", (panel_x + 10, y_offset), 0.7, (255, 255, 255), 2
        )

        # Battery
        battery = telemetry_data.get("battery", -1)
        if battery >= 0:
            y_offset += 25
            battery_color = (0, 255, 0)  # Green
            if battery <= 15:
                battery_color = (0, 0, 255)  # Red
            elif battery <= 30:
                battery_color = (0, 165, 255)  # Orange

            self.add_text_to_frame(
                overlay, f"Battery: {battery}%", (panel_x + 10, y_offset), 0.6, battery_color, 1
            )

        # Height (if available)
        height = telemetry_data.get("height")
        if height is not None:
            y_offset += 25
            self.add_text_to_frame(
                overlay, f"Height: {height}cm", (panel_x + 10, y_offset), 0.6, (255, 255, 255), 1
            )

        # Speed information
        speed_x = telemetry_data.get("vgx")
        speed_y = telemetry_data.get("vgy")
        speed_z = telemetry_data.get("vgz")
        if all(v is not None for v in [speed_x, speed_y, speed_z]):
            y_offset += 25
            speed_text = f"Speed: X:{speed_x} Y:{speed_y} Z:{speed_z}"
            self.add_text_to_frame(
                overlay, speed_text, (panel_x + 10, y_offset), 0.6, (255, 255, 255), 1
            )

            # Display speed vector visually (optional)
            if abs(speed_x) > 3 or abs(speed_y) > 3:  # Only if speed is above threshold
                indicator_x = panel_x + 125
                indicator_y = y_offset + 15
                indicator_scale = 2.0

                # Direction arrow
                end_x = int(indicator_x + speed_x * indicator_scale)
                end_y = int(indicator_y - speed_y * indicator_scale)
                cv2.arrowedLine(
                    overlay,
                    (indicator_x, indicator_y),
                    (end_x, end_y),
                    (0, 255, 255),
                    2,
                    tipLength=0.3,
                )

        # Attitude information
        pitch = telemetry_data.get("pitch")
        roll = telemetry_data.get("roll")
        yaw = telemetry_data.get("yaw")
        if all(v is not None for v in [pitch, roll, yaw]):
            y_offset += 25
            attitude_text = f"Attitude: P:{pitch}° R:{roll}° Y:{yaw}°"
            self.add_text_to_frame(
                overlay, attitude_text, (panel_x + 10, y_offset), 0.6, (255, 255, 255), 1
            )

        # Error information
        error_count = telemetry_data.get("error_count", 0)
        if error_count > 0:
            y_offset += 25
            self.add_text_to_frame(
                overlay, f"Errors: {error_count}", (panel_x + 10, y_offset), 0.6, (0, 0, 255), 1
            )

        # Connection status
        y_offset += 25
        connection_status = telemetry_data.get("connection_status", "Unknown")
        # Convert any remaining Japanese status to English
        if connection_status == "Connected" or connection_status == "接続中":
            connection_status = "Connected"
        elif connection_status == "Disconnected" or connection_status == "切断":
            connection_status = "Disconnected"
        elif connection_status == "Frame Error" or connection_status == "フレーム取得失敗":
            connection_status = "Frame Error"
        elif connection_status == "Not Connected" or connection_status == "未接続":
            connection_status = "Not Connected"

        conn_color = (0, 255, 0) if connection_status == "Connected" else (0, 0, 255)
        self.add_text_to_frame(
            overlay, f"Status: {connection_status}", (panel_x + 10, y_offset), 0.6, conn_color, 1
        )

        # Frame statistics
        y_offset += 25
        self.add_text_to_frame(
            overlay, f"FPS: {self.fps:.1f}", (panel_x + 10, y_offset), 0.6, (255, 255, 255), 1
        )

        # Blend overlay (semi-transparent)
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        return frame

    def toggle_info_display(self):
        """Toggle display of information overlay"""
        self.show_info = not self.show_info
        return self.show_info

    def release(self):
        """Release all resources"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
        print("Video stream closed successfully")


# 単体テスト用コード
if __name__ == "__main__":
    stream = VideoStream()
    if stream.connect():
        try:
            print("Displaying video stream... Press 'q' to exit")
            while True:
                ret, frame = stream.read_frame()
                if not ret:
                    print("Failed to read frame")
                    time.sleep(0.1)
                    continue

                fps = stream.calculate_fps()
                if fps > 0:
                    print(f"Current FPS: {fps:.2f}")

                key = stream.display_frame(frame)
                if key & 0xFF in (27, ord("q")):  # ESC or q to exit
                    print("User terminated")
                    break

        finally:
            stream.release()
    else:
        print("Failed to start streaming")
