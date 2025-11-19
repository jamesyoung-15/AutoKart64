import subprocess
import time
import enum
from dataclasses import dataclass


class KeyCode(enum.Enum):
    """Key codes for ydotool corresponding to keyboard keys."""

    UP = "103"
    DOWN = "108"
    LEFT = "105"
    RIGHT = "106"
    F7 = "65"
    LEFT_SHIFT = "42"
    LEFT_CTRL = "29"


@dataclass(frozen=True)
class NumKeyCode:
    """Key codes for number keys 0-9 for ydotool."""

    ZERO: str = "11"
    ONE: str = "2"
    TWO: str = "3"
    THREE: str = "4"
    FOUR: str = "5"
    FIVE: str = "6"
    SIX: str = "7"
    SEVEN: str = "8"
    EIGHT: str = "9"
    NINE: str = "10"


class KeyboardController:
    def __init__(self) -> None:
        self.current_action_process: subprocess.Popen | None = None

    def press_keys(self, key_codes: list[str], duration: float | None = None) -> None:
        """
        Press multiple keys simultaneously using ydotool.

        Args:
            key_codes (list[str]): List of key codes to press.
            duration (float | None): Optional duration in mss to hold the keys.
        """
        press_key_cmd = ["ydotool", "key"]
        press_key_cmd.extend(key_codes)
        subprocess.run(press_key_cmd)

        release_duration = 0.01
        if duration is not None:
            press_duration = duration / 1000 - release_duration
            if press_duration > 0:
                time.sleep(press_duration)

        self.release_keys(key_codes)
        time.sleep(release_duration)  # ensure keys are released properly

    def release_keys(self, key_codes: list[str]) -> None:
        """
        Release multiple keys using ydotool.

        Args:
            key_codes (list[str]): List of key codes to release.
        """
        release_key_cmd = ["ydotool", "key"]
        for key_code in key_codes:
            release_key_cmd.append(key_code + ":0")
        subprocess.run(release_key_cmd)

    def press_keys_non_blocking(self, key_codes: list[str], duration: int) -> None:
        """
        Press multiple keys simultaneously using ydotool without blocking.

        Args:
            key_codes (list[str]): List of key codes to press.
            duration (int): Duration in ms to hold the keys.
        """
        # Cancel any ongoing action by waiting for it to complete
        if self.current_action_process is not None:
            self.current_action_process.wait()
            self.current_action_process = None

        # Press keys
        press_key_cmd = ["ydotool", "key"]
        press_key_cmd.extend(key_codes)
        subprocess.run(press_key_cmd)

        # Schedule key release in background
        release_duration = 0.01
        press_duration = (duration / 1000) - release_duration

        if press_duration > 0:
            # Create a shell command that sleeps then releases keys
            release_key_cmd = ["ydotool", "key"]
            for key_code in key_codes:
                release_key_cmd.append(key_code + ":0")

            # Construct full command with sleep
            full_cmd = f"sleep {press_duration} && {' '.join(release_key_cmd)}"

            self.current_action_process = subprocess.Popen(
                full_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            # Release immediately
            self.release_keys(key_codes)

    def drive_forward_nonblocking(self, duration: int) -> None:
        """
        Press left shift to drive forward in Mario Kart 64 without blocking.
        """
        self.press_keys_non_blocking([KeyCode.LEFT_SHIFT.value], duration=duration)

    def drive_forward_left_nonblocking(self, duration: int) -> None:
        """
        Press left shift and left arrow to drive forward left in Mario Kart 64 without blocking.
        """
        self.press_keys_non_blocking(
            [KeyCode.LEFT_SHIFT.value, KeyCode.LEFT.value], duration=duration
        )

    def drive_forward_right_nonblocking(self, duration: int) -> None:
        """
        Press left shift and right arrow to drive forward right in Mario Kart 64 without blocking.
        """
        self.press_keys_non_blocking(
            [KeyCode.LEFT_SHIFT.value, KeyCode.RIGHT.value], duration=duration
        )

    def drive_forward(self, duration: float | None = None) -> None:
        """
        Press left shift to drive forward in Mario Kart 64.

        Args:
            duration (float | None): Optional duration in ms to hold the key.
        """
        self.press_keys([KeyCode.LEFT_SHIFT.value], duration=duration)

    def brake(self, duration: float | None = None) -> None:
        """
        Press left ctrl to brake in Mario Kart 64.

        Args:
            duration (float | None): Optional duration in ms to hold the key.
        """
        self.press_keys([KeyCode.LEFT_CTRL.value], duration=duration)

    def drive_forward_left(self, duration: float | None = None) -> None:
        """
        Press left shift and left arrow to drive forward left in Mario Kart 64.

        Args:
            duration (float | None): Optional duration in ms to hold the key.
        """
        self.press_keys(
            [KeyCode.LEFT_SHIFT.value, KeyCode.LEFT.value], duration=duration
        )

    def drive_forward_right(self, duration: float | None = None) -> None:
        """
        Press left shift and right arrow to drive forward right in Mario Kart 64.

        Args:
            duration (float | None): Optional duration in ms to hold the key.
        """
        self.press_keys(
            [KeyCode.LEFT_SHIFT.value, KeyCode.RIGHT.value], duration=duration
        )

    def load_state(self, slot: int = 0) -> None:
        """
        Load a save state in M64Py using F7 + slot number.

        Args:
            slot (int): Save state slot number (0-9).
        """
        if slot < 0 or slot > 9:
            raise ValueError("Slot number must be between 0 and 9.")
        num_key_codes = [
            NumKeyCode.ZERO,
            NumKeyCode.ONE,
            NumKeyCode.TWO,
            NumKeyCode.THREE,
            NumKeyCode.FOUR,
            NumKeyCode.FIVE,
            NumKeyCode.SIX,
            NumKeyCode.SEVEN,
            NumKeyCode.EIGHT,
            NumKeyCode.NINE,
        ]
        slot_key_code = num_key_codes[slot]
        self.press_keys([slot_key_code], duration=12)
        self.press_keys([KeyCode.F7.value], duration=12)

    def release_all(self) -> None:
        """
        Release all keys to ensure no keys are stuck.
        """
        all_keys = [key.value for key in KeyCode]
        self.release_keys(all_keys)


if __name__ == "__main__":
    controller = KeyboardController()
    fps = 30
    frames_per_action = 4
    time_per_action = frames_per_action / fps
    delay = time_per_action * 1000  # Convert to milliseconds

    time.sleep(3)  # Time to switch to the target application

    actions = {
        "forward": controller.drive_forward,
        # "brake": controller.brake,
        "forward_left": controller.drive_forward_left,
        "forward_right": controller.drive_forward_right,
    }

    try:
        while True:
            # choose random action
            # import random
            # action = random.choice(list(actions.values()))
            # action(duration=delay)
            controller.load_state(slot=0)
            time.sleep(10)
    except KeyboardInterrupt:
        print("Exiting and releasing all keys.")
    finally:
        controller.release_all()
