#!/usr/bin/env python3
"""
Main entry point for the Tello XR prototype.
"""

def main():
    print("Tello XR prototype initialized!")
    
    # Import verification
    try:
        import numpy as np
        import cv2
        print(f"NumPy version: {np.__version__}")
        print(f"OpenCV version: {cv2.__version__}")
        print("All dependencies loaded successfully!")
    except ImportError as e:
        print(f"Error importing dependencies: {e}")

if __name__ == "__main__":
    main()