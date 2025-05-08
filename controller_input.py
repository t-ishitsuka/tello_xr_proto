"""
Controller Input Module for Tello XR Prototype
This module handles game controller detection, initialization, and input processing.
"""

import json
import logging
import time
import os

import pygame


class ControllerManager:
    """Manages game controller detection and initialization."""

    def __init__(self, debug: bool = False, config_file: str = None):
        """
        Initialize the controller manager.

        Args:
            debug: Enable debug output
            config_file: Path to controller configuration file (JSON)
        """
        self.debug = debug
        self.controllers = {}  # Dictionary of initialized controllers
        self.selected_controller = None  # Currently active controller
        self._setup_logging()
        self._initialize_pygame()
        
        # 設定関連の初期化
        self.config = {}
        self.config_file = config_file
        self.load_config()

    def _setup_logging(self):
        """Set up logging configuration."""
        log_level = logging.DEBUG if self.debug else logging.INFO
        logging.basicConfig(
            level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger("ControllerManager")

    def _initialize_pygame(self):
        """Initialize pygame and the joystick module."""
        try:
            pygame.init()
            pygame.joystick.init()
            self.logger.info("Pygame initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Pygame: {e}")
            raise

    def load_config(self):
        """
        設定ファイルを読み込む。
        ファイルが指定されていない場合やエラー時はデフォルト設定を使用
        """
        # デフォルト設定を初期化
        self.config = self.get_default_config()
        
        if not self.config_file:
            self.logger.info("設定ファイルが指定されていません。デフォルト設定を使用します")
            return
            
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # デフォルト設定にユーザー設定を上書き
                    self.config.update(user_config)
                    self.logger.info(f"設定ファイルを読み込みました: {self.config_file}")
            else:
                self.logger.warning(f"設定ファイルが見つかりません: {self.config_file}")
                self.save_default_config()
        except Exception as e:
            self.logger.error(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
    
    def get_default_config(self):
        """
        デフォルトのコントローラー設定を返す
        """
        return {
            "deadzone": 0.15,
            "axis_mapping": {
                "move_x": 0,      # 左スティックX軸: 左右移動
                "move_y": 1,      # 左スティックY軸: 前後移動
                "move_z": 3,      # 右スティックY軸: 上下移動
                "rotation": 2     # 右スティックX軸: 回転
            },
            "button_mapping": {
                "takeoff": 0,     # A/Xボタン: 離陸
                "land": 1,        # B/Oボタン: 着陸
                "emergency": 2,   # X/□ボタン: 緊急停止
                "photo": 3        # Y/△ボタン: 写真撮影
            },
            "invert_axis": {
                "move_y": True,   # 前後移動は反転（前進が-1）
                "move_z": True    # 上下移動は反転（上昇が-1）
            },
            "sensitivity": {
                "move_xy": 1.0,   # 水平移動の感度
                "move_z": 0.7,    # 垂直移動の感度
                "rotation": 0.8   # 回転の感度
            }
        }
    
    def save_default_config(self):
        """
        デフォルト設定をファイルに保存する
        """
        if not self.config_file:
            self.logger.warning("設定ファイルパスが指定されていないため、保存できません")
            return False
            
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
            
            # デフォルト設定を保存
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.get_default_config(), f, indent=4, ensure_ascii=False)
            self.logger.info(f"デフォルト設定をファイルに保存しました: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"設定ファイルの保存中にエラーが発生しました: {e}")
            return False

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
                        "joystick": joystick,
                        "name": joystick.get_name(),
                        "axes": joystick.get_numaxes(),
                        "buttons": joystick.get_numbuttons(),
                        "hats": joystick.get_numhats(),
                    }
                    self.controllers[controller_id] = controller_info
                    self.logger.info(
                        f"Initialized controller {i}: {controller_info['name']} "
                        f"(Axes: {controller_info['axes']}, Buttons: {controller_info['buttons']})"
                    )

                    # If this is the first controller, select it automatically
                    if self.selected_controller is None:
                        self.selected_controller = controller_id
                        self.logger.info(
                            f"Automatically selected controller: {controller_info['name']}"
                        )

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
            controller_name = self.controllers[controller_id]["name"]
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
        return [(controller_id, info["name"]) for controller_id, info in self.controllers.items()]

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
                    self.selected_controller = (
                        next(iter(self.controllers)) if self.controllers else None
                    )
                    if self.selected_controller:
                        controller_name = self.controllers[self.selected_controller]["name"]
                        self.logger.info(
                            f"Automatically selected new controller: {controller_name}"
                        )
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
            joystick = self.controllers[self.selected_controller]["joystick"]
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
            joystick = self.controllers[self.selected_controller]["joystick"]
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
            joystick = self.controllers[self.selected_controller]["joystick"]
            if hat_index >= joystick.get_numhats():
                self.logger.warning(f"Hat index {hat_index} out of range")
                return (0, 0)

            return joystick.get_hat(hat_index)
        except Exception as e:
            self.logger.error(f"Error reading hat {hat_index}: {e}")
            return (0, 0)

    def get_controller_input(
        self,
    ) -> dict[str, list[float] | list[bool] | list[tuple[int, int]]] | None:
        """
        Get the current input state from the selected controller.

        Returns:
            Dictionary with controller input states (axes, buttons, hats) or None if no controller is selected
        """
        if not self.is_controller_available():
            return None

        # Process pygame events to ensure we have the latest state
        pygame.event.pump()

        joystick = self.controllers[self.selected_controller]["joystick"]
        controller_input = {"axes": [], "buttons": [], "hats": []}

        # Get axis values (typically -1.0 to 1.0)
        for i in range(joystick.get_numaxes()):
            controller_input["axes"].append(joystick.get_axis(i))

        # Get button values (0 or 1)
        for i in range(joystick.get_numbuttons()):
            controller_input["buttons"].append(joystick.get_button(i) == 1)

        # Get hat values (tuple of int values, typically (-1, 0, 1))
        for i in range(joystick.get_numhats()):
            controller_input["hats"].append(joystick.get_hat(i))

        return controller_input

    def get_normalized_input(self) -> dict[str, dict[str, float | bool]] | None:
        """
        Get normalized input values mapped to more intuitive controls.
        Normalizes controller inputs based on configuration settings.

        Returns:
            Dictionary with movement, rotation, and button states or None if no controller is selected
        """
        if not self.is_controller_available():
            return None

        raw_input = self.get_controller_input()
        if not raw_input:
            return None

        # 設定から必要な値を取得
        deadzone = self.config.get("deadzone", 0.15)
        axis_mapping = self.config.get("axis_mapping", {
            "move_x": 0, "move_y": 1, "move_z": 3, "rotation": 2
        })
        button_mapping = self.config.get("button_mapping", {
            "takeoff": 0, "land": 1, "emergency": 2, "photo": 3
        })
        invert_axis = self.config.get("invert_axis", {
            "move_y": True, "move_z": True
        })
        sensitivity = self.config.get("sensitivity", {
            "move_xy": 1.0, "move_z": 0.7, "rotation": 0.8
        })
        
        # キャリブレーションデータの取得
        calibration = self.config.get("calibration", {})
        axis_offsets = calibration.get("axis_offsets", {})

        # 初期化
        movement = {
            "x": 0.0,  # Left/Right movement
            "y": 0.0,  # Forward/Backward movement
            "z": 0.0,  # Up/Down movement
            "rotation": 0.0,  # Yaw rotation
        }

        buttons = {
            "takeoff": False,
            "land": False,
            "emergency": False,
            "photo": False,
        }

        # 軸の入力を適用（設定に基づく）
        axes = raw_input["axes"]
        if len(axes) > 0:
            # 各動きに対応する軸を適用
            for key, axis_index in axis_mapping.items():
                if axis_index < len(axes):
                    # 生の軸の値を取得
                    value = axes[axis_index]
                    
                    # キャリブレーションオフセットを適用（もし存在すれば）
                    offset = float(axis_offsets.get(str(axis_index), 0))
                    value = value - offset
                    
                    # 軸の反転が設定されている場合は反転
                    if key in invert_axis and invert_axis[key]:
                        value = -value
                    
                    # 感度の適用
                    if key in ["move_x", "move_y"]:
                        value *= sensitivity.get("move_xy", 1.0)
                    elif key == "move_z":
                        value *= sensitivity.get("move_z", 0.7)
                    elif key == "rotation":
                        value *= sensitivity.get("rotation", 0.8)
                    
                    # 対応する動きに値を割り当て
                    if key == "move_x":
                        movement["x"] = value
                    elif key == "move_y":
                        movement["y"] = value
                    elif key == "move_z":
                        movement["z"] = value
                    elif key == "rotation":
                        movement["rotation"] = value

        # ボタンの入力を適用（設定に基づく）
        button_states = raw_input["buttons"]
        if len(button_states) > 0:
            for key, button_index in button_mapping.items():
                if button_index < len(button_states):
                    buttons[key] = button_states[button_index]

        # デッドゾーンを適用
        for key in movement:
            if abs(movement[key]) < deadzone:
                movement[key] = 0.0
            elif movement[key] > 0:
                # デッドゾーン以上の値を0-1の範囲に再マッピング
                movement[key] = (movement[key] - deadzone) / (1 - deadzone)
            else:
                # デッドゾーン以上の値を-1-0の範囲に再マッピング
                movement[key] = (movement[key] + deadzone) / (1 - deadzone)

        return {
            "movement": movement,
            "buttons": buttons,
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
            joystick = self.controllers[self.selected_controller]["joystick"]
            inputs = {
                "axes": [joystick.get_axis(i) for i in range(joystick.get_numaxes())],
                "buttons": [joystick.get_button(i) for i in range(joystick.get_numbuttons())],
                "hats": [joystick.get_hat(i) for i in range(joystick.get_numhats())],
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

    def calibrate_controller(self, samples=10, delay=0.1):
        """
        コントローラーのキャリブレーションを実行する。
        スティック軸の中心位置を計測して、オフセット値を設定に保存する。

        Args:
            samples: キャリブレーションのためのサンプル数
            delay: サンプル間の遅延（秒）

        Returns:
            bool: キャリブレーションが成功したらTrue
        """
        if not self.is_controller_available():
            self.logger.warning("キャリブレーション失敗: コントローラーが接続されていません")
            return False

        try:
            self.logger.info(f"コントローラーのキャリブレーションを開始します（{samples}サンプル）")
            print("コントローラーのスティックを放し、中立位置に戻してください...")
            
            # キャリブレーション前の待機時間
            time.sleep(1.0)
            
            # 軸のオフセット値を測定
            axis_offsets = {}
            joystick = self.controllers[self.selected_controller]["joystick"]
            num_axes = joystick.get_numaxes()
            
            # 各軸のオフセットサンプルを収集
            axis_samples = {i: [] for i in range(num_axes)}
            
            for sample in range(samples):
                pygame.event.pump()  # イベントを処理して最新の状態を取得
                
                for axis in range(num_axes):
                    axis_samples[axis].append(joystick.get_axis(axis))
                
                time.sleep(delay)
                print(f"サンプル {sample+1}/{samples} 収集中...", end="\r")
            
            print("\nキャリブレーション完了!")
            
            # 各軸のオフセット平均値を計算
            for axis in range(num_axes):
                if axis_samples[axis]:
                    axis_offsets[str(axis)] = sum(axis_samples[axis]) / len(axis_samples[axis])
            
            # 設定に保存
            if "calibration" not in self.config:
                self.config["calibration"] = {}
            
            self.config["calibration"]["axis_offsets"] = axis_offsets
            self.logger.info(f"軸オフセット値を設定しました: {axis_offsets}")
            
            # 設定ファイルにキャリブレーション結果を保存
            self._save_config()
            
            return True
            
        except Exception as e:
            self.logger.error(f"キャリブレーション中にエラーが発生しました: {e}")
            return False
    
    def _save_config(self):
        """現在の設定をファイルに保存する"""
        if not self.config_file:
            self.logger.warning("設定ファイルパスが指定されていないため、設定を保存できません")
            return False
            
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
            
            # 設定を保存
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"設定をファイルに保存しました: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"設定ファイルの保存中にエラーが発生しました: {e}")
            return False


# Simple test function
def test_controller_detection():
    """Test the controller detection functionality."""
    # 設定ファイルのパスを指定
    config_path = "config/controller_config.json"
    manager = ControllerManager(debug=True, config_file=config_path)

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
            print(f"\n設定: {manager.config}")

            # キャリブレーションオプションの提供
            print("\nオプション:")
            print("1: 入力テスト")
            print("2: コントローラーキャリブレーション")
            print("q: 終了")
            choice = input("選択してください: ")

            if choice == "1":
                run_input_test(manager)
            elif choice == "2":
                # キャリブレーション実行
                print("\nキャリブレーションを開始します...")
                if manager.calibrate_controller(samples=15):
                    print("キャリブレーションが完了しました！")
                    print("設定ファイルに保存されました。")
                else:
                    print("キャリブレーションに失敗しました。")
                
                # キャリブレーション後の入力テスト
                run_input_test(manager)
            else:
                print("終了します。")
    else:
        print("No controllers detected.")

    manager.cleanup()


def run_input_test(manager):
    """コントローラー入力のテストを実行する"""
    print("\nPress Ctrl+C to exit")
    print("Reading controller input (live display)...")
    try:
        while True:
            # Get and display raw controller input
            raw_input = manager.get_controller_input()
            if raw_input:
                # Clear the line using ANSI escape code
                print("\033[K", end="\r")  # Clear to the end of line
                axes_str = ", ".join([f"{val:.2f}" for val in raw_input["axes"]])
                buttons_str = "".join(["1" if b else "0" for b in raw_input["buttons"]])
                print(f"Axes: [{axes_str}] | Buttons: {buttons_str}", end="\r")

            # Process normalized input for drone control
            norm_input = manager.get_normalized_input()
            if norm_input and hasattr(time, "monotonic") and int(time.monotonic()) % 3 == 0:
                # Every ~3 seconds, show the normalized values
                m = norm_input["movement"]
                b = norm_input["buttons"]
                print("\nNormalized Input:")
                print(
                    f"  Movement: X:{m['x']:.2f} Y:{m['y']:.2f} Z:{m['z']:.2f} Rotation:{m['rotation']:.2f}"
                )
                print(
                    f"  Buttons: Takeoff:{b['takeoff']} Land:{b['land']} Emergency:{b['emergency']} Photo:{b['photo']}"
                )

            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nTest ended by user")


if __name__ == "__main__":
    # Use the test function to see controller inputs
    test_controller_detection()
