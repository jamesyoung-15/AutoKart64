import evdev


def see_inputs():
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    keyboard = None
    for idx, device in enumerate(devices):
        print(f"Device {idx}: {device.path} - {device.name}")

    keyboard_selection = input("Select the device number for the keyboard to monitor: ")
    try:
        keyboard_idx = int(keyboard_selection)
        keyboard = devices[keyboard_idx]
    except (ValueError, IndexError):
        print("Invalid selection. Exiting.")
        return

    if keyboard:
        try:
            print(
                f"Listening to keyboard events from: {keyboard.path} - {keyboard.name}"
            )
            for event in keyboard.read_loop():
                if event.type == evdev.ecodes.EV_KEY:
                    key_event = evdev.categorize(event)
                    print(key_event)
        except KeyboardInterrupt:
            print("Exiting...")
        except Exception as e:
            print(f"Error reading from device: {e}")


if __name__ == "__main__":
    see_inputs()
