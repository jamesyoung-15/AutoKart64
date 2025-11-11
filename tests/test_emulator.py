import time
import threading

from emulator.m64 import M64Py
from configs.emulator_consts import M64_LIB_PATH, M64_PLUGIN_PATH, M64_ROM_PATH


def test_emulator_integration():
    # Initialize the emulator
    emulator = M64Py()
    thread1 = threading.Thread(
        target=emulator.run_emulator, args=(M64_LIB_PATH, M64_PLUGIN_PATH, M64_ROM_PATH)
    )
    thread1.start()

    time.sleep(5)
    assert emulator.get_game_started() is True

    emulator.stop_emulator()
    thread1.join()
