"""
Controller Input Module for Tello XR Prototype
This module handles game controller detection, initialization, and input processing.
"""

import logging
import time

import pygame


class ControllerManager:
    """Manages game controller detection and initialization."""
    
    def __init__(self, debug: bool = False):
        """
        Initialize the controller manager.
        
        Args:
            debug: Enable debug output
        """
        self.debug = debug
        self.controllers = {}  # Dictionary of initialized controllers
        self.selected_controller = None  # Currently active controller
        self._setup_logging()
        self._initialize_pygame()
        
    def _setup_logging(self):
        """Set up logging configuration."""
        log_level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('ControllerManager')
    
    def _initialize_pygame(self):
        """Initialize pygame and the joystick module."""
        try:
            pygame.init()
            pygame.joystick.init()
            self.logger.info("Pygame initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Pygame: {e}")
            raise
    
    def detect_controllers(self) -> int:
        """
        Detect all connected controllers.
        
        Returns:
            Number of controllers detected
        """
        try:
            num_controllers = pygame.joystick.get_count()
            self.logger.info(f"Detected {num_controllers} controller(s)")
            
            # Initialize all detected controllers
            for i in range(num_controllers):
                try:
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()
                    controller_id = joystick.get_instance_id()
                    controller_info = {
                        'joystick': joystick,
                        'name': joystick.get_name(),
                        'axes': joystick.get_numaxes(),
                        'buttons': joystick.get_numbuttons(),
                        'hats': joystick.get_numhats()
                    }
                    self.controllers[controller_id] = controller_info
                    self.logger.info(
                        f"Initialized controller {i}: {controller_info['name']} "
                        f"(Axes: {controller_info['axes']}, Buttons: {controller_info['buttons']})"
                    )
                    
                    # If this is the first controller, select it automatically
                    if self.selected_controller is None:
                        self.selected_controller = controller_id
                        self.logger.info(f"Automatically selected controller: {controller_info['name']}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to initialize controller {i}: {e}")
            
            return num_controllers
        except Exception as e:
            self.logger.error(f"Error detecting controllers: {e}")
            return 0
    
    def select_controller(self, controller_id: int) -> bool:
        """
        Select a specific controller to use.
        
        Args:
            controller_id: The ID of the controller to select
            
        Returns:
            True if selection was successful, False otherwise
        """
        if controller_id in self.controllers:
            self.selected_controller = controller_id
            controller_name = self.controllers[controller_id]['name']
            self.logger.info(f"Selected controller: {controller_name}")
            return True
        else:
            self.logger.warning(f"Controller ID {controller_id} not found")
            return False
    
    def get_controller_names(self) -> list[tuple[int, str]]:
        """
        Get names of all detected controllers.
        
        Returns:
            List of (controller_id, name) tuples
        """
        return [(controller_id, info['name']) for controller_id, info in self.controllers.items()]
    
    def handle_events(self):
        """Process pygame events to detect controller connections/disconnections."""
        for event in pygame.event.get():
            if event.type == pygame.JOYDEVICEADDED:
                self.logger.info(f"Controller connected: {event.device_index}")
                # Re-detect controllers to include the new one
                self.detect_controllers()
            
            elif event.type == pygame.JOYDEVICEREMOVED:
                self.logger.info(f"Controller disconnected: {event.instance_id}")
                # Remove the disconnected controller
                if event.instance_id in self.controllers:
                    del self.controllers[event.instance_id]
                    
                # If the selected controller was removed, select a new one if available
                if event.instance_id == self.selected_controller:
                    self.selected_controller = next(iter(self.controllers)) if self.controllers else None
                    if self.selected_controller:
                        controller_name = self.controllers[self.selected_controller]['name']
                        self.logger.info(f"Automatically selected new controller: {controller_name}")
                    else:
                        self.logger.warning("No controllers available")
    
    def is_controller_available(self) -> bool:
        """
        Check if any controller is available and selected.
        
        Returns:
            True if a controller is selected and available
        """
        return self.selected_controller is not None
    
    def get_controller_info(self) -> dict | None:
        """
        Get information about the currently selected controller.
        
        Returns:
            Dictionary with controller information or None if no controller is selected
        """
        if not self.is_controller_available():
            return None
        
        return self.controllers.get(self.selected_controller)
    
    def read_axis(self, axis_index: int) -> float:
        """
        Read the value of a specific axis from the selected controller.
        
        Args:
            axis_index: Index of the axis to read
            
        Returns:
            Axis value between -1.0 and 1.0, or 0.0 if no controller is available
        """
        if not self.is_controller_available():
            return 0.0
            
        try:
            joystick = self.controllers[self.selected_controller]['joystick']
            if axis_index >= joystick.get_numaxes():
                self.logger.warning(f"Axis index {axis_index} out of range")
                return 0.0
            
            return joystick.get_axis(axis_index)
        except Exception as e:
            self.logger.error(f"Error reading axis {axis_index}: {e}")
            return 0.0
    
    def read_button(self, button_index: int) -> bool:
        """
        Read the state of a specific button from the selected controller.
        
        Args:
            button_index: Index of the button to read
            
        Returns:
            True if the button is pressed, False otherwise or if no controller is available
        """
        if not self.is_controller_available():
            return False
            
        try:
            joystick = self.controllers[self.selected_controller]['joystick']
            if button_index >= joystick.get_numbuttons():
                self.logger.warning(f"Button index {button_index} out of range")
                return False
            
            return bool(joystick.get_button(button_index))
        except Exception as e:
            self.logger.error(f"Error reading button {button_index}: {e}")
            return False
    
    def read_hat(self, hat_index: int) -> tuple[int, int]:
        """
        Read the values of a hat (D-pad) from the selected controller.
        
        Args:
            hat_index: Index of the hat to read
            
        Returns:
            Tuple of (x, y) values, each either -1, 0, or 1, or (0, 0) if no controller is available
        """
        if not self.is_controller_available():
            return (0, 0)
            
        try:
            joystick = self.controllers[self.selected_controller]['joystick']
            if hat_index >= joystick.get_numhats():
                self.logger.warning(f"Hat index {hat_index} out of range")
                return (0, 0)
            
            return joystick.get_hat(hat_index)
        except Exception as e:
            self.logger.error(f"Error reading hat {hat_index}: {e}")
            return (0, 0)
    
    def get_controller_input(self) -> dict[str, list[float] | list[bool] | list[tuple[int, int]]] | None:
        """
        Get the current input state from the selected controller.
        
        Returns:
            Dictionary with controller input states (axes, buttons, hats) or None if no controller is selected
        """
        if not self.is_controller_available():
            return None
        
        # Process pygame events to ensure we have the latest state
        pygame.event.pump()
        
        joystick = self.controllers[self.selected_controller]['joystick']
        controller_input = {
            'axes': [],
            'buttons': [],
            'hats': []
        }
        
        # Get axis values (typically -1.0 to 1.0)
        for i in range(joystick.get_numaxes()):
            controller_input['axes'].append(joystick.get_axis(i))
        
        # Get button values (0 or 1)
        for i in range(joystick.get_numbuttons()):
            controller_input['buttons'].append(joystick.get_button(i) == 1)
        
        # Get hat values (tuple of int values, typically (-1, 0, 1))
        for i in range(joystick.get_numhats()):
            controller_input['hats'].append(joystick.get_hat(i))
        
        return controller_input
    
    def get_normalized_input(self) -> dict[str, dict[str, float | bool]] | None:
        """
        Get normalized input values mapped to more intuitive controls.
        Normalizes common controller layouts to standard movement controls.
        
        Returns:
            Dictionary with movement, rotation, and button states or None if no controller is selected
        """
        if not self.is_controller_available():
            return None
            
        raw_input = self.get_controller_input()
        if not raw_input:
            return None
            
        # Default mapping (works with common controllers like Xbox/PS)
        # This can be customized based on specific controllers
        movement = {
            'x': 0.0,  # Left/Right movement
            'y': 0.0,  # Forward/Backward movement
            'z': 0.0,  # Up/Down movement
            'rotation': 0.0,  # Yaw rotation
        }
        
        buttons = {
            'takeoff': False,
            'land': False,
            'emergency': False,
        }
        
        # Apply left stick for horizontal movement (typically axes 0, 1)
        if len(raw_input['axes']) >= 2:
            movement['x'] = raw_input['axes'][0]  # Left stick X: left/right
            movement['y'] = -raw_input['axes'][1]  # Left stick Y: forward/backward (inverted)
            
        # Apply right stick for rotation and vertical movement (typically axes 2, 3)
        if len(raw_input['axes']) >= 4:
            movement['rotation'] = raw_input['axes'][2]  # Right stick X: yaw rotation
            movement['z'] = -raw_input['axes'][3]  # Right stick Y: up/down (inverted)
            
        # Map buttons (common layout, can be customized)
        if len(raw_input['buttons']) >= 4:
            buttons['takeoff'] = raw_input['buttons'][0]  # A/X button
            buttons['land'] = raw_input['buttons'][1]  # B/Circle button
            buttons['emergency'] = raw_input['buttons'][2]  # X/Square button
            
        # Apply deadzone to reduce drift
        deadzone = 0.15
        for key in movement:
            if abs(movement[key]) < deadzone:
                movement[key] = 0.0
        
        return {
            'movement': movement,
            'buttons': buttons,
        }
    
    def read_all_inputs(self) -> dict:
        """
        Read all inputs from the selected controller.
        
        Returns:
            Dictionary with all controller inputs, or empty dict if no controller is available
        """
        if not self.is_controller_available():
            return {}
            
        try:
            joystick = self.controllers[self.selected_controller]['joystick']
            inputs = {
                'axes': [joystick.get_axis(i) for i in range(joystick.get_numaxes())],
                'buttons': [joystick.get_button(i) for i in range(joystick.get_numbuttons())],
                'hats': [joystick.get_hat(i) for i in range(joystick.get_numhats())]
            }
            
            # Update events to ensure we're capturing the latest button states
            pygame.event.pump()
            
            return inputs
        except Exception as e:
            self.logger.error(f"Error reading all inputs: {e}")
            return {}
    
    def cleanup(self):
        """Clean up pygame resources."""
        pygame.joystick.quit()
        pygame.quit()
        self.logger.info("Pygame resources cleaned up")


# Simple test function
def test_controller_detection():
    """Test the controller detection functionality."""
    manager = ControllerManager(debug=True)
    
    print("Detecting controllers...")
    num_controllers = manager.detect_controllers()
    
    if num_controllers > 0:
        print(f"\nDetected {num_controllers} controller(s):")
        for controller_id, name in manager.get_controller_names():
            print(f"ID: {controller_id}, Name: {name}")
        
        print("\nSelected controller info:")
        info = manager.get_controller_info()
        if info:
            print(f"Name: {info['name']}")
            print(f"Axes: {info['axes']}")
            print(f"Buttons: {info['buttons']}")
            print(f"Hats: {info['hats']}")
            
            print("\nPress Ctrl+C to exit")
            print("Reading controller input (live display)...")
            try:
                while True:
                    # Get and display raw controller input
                    raw_input = manager.get_controller_input()
                    if raw_input:
                        # Clear the line using ANSI escape code
                        print("\033[K", end="\r")  # Clear to the end of line
                        axes_str = ", ".join([f"{val:.2f}" for val in raw_input['axes']])
                        buttons_str = "".join(["1" if b else "0" for b in raw_input['buttons']])
                        print(f"Axes: [{axes_str}] | Buttons: {buttons_str}", end="\r")
                    
                    # Process normalized input for drone control
                    norm_input = manager.get_normalized_input()
                    if norm_input and hasattr(time, 'monotonic') and int(time.monotonic()) % 3 == 0:
                        # Every ~3 seconds, show the normalized values
                        m = norm_input['movement']
                        b = norm_input['buttons']
                        print("\nNormalized Input:")
                        print(f"  Movement: X:{m['x']:.2f} Y:{m['y']:.2f} Z:{m['z']:.2f} Rotation:{m['rotation']:.2f}")
                        print(f"  Buttons: Takeoff:{b['takeoff']} Land:{b['land']} Emergency:{b['emergency']}")
                        
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nTest ended by user")
    else:
        print("No controllers detected.")
    
    manager.cleanup()


if __name__ == "__main__":
    # Use the test function to see controller inputs
    test_controller_detection()