from emulator.m64 import M64Py
import threading
from configs.emulator_consts import M64_LIB_PATH, M64_PLUGIN_PATH, M64_ROM_PATH

emulator = M64Py()
thread1 = threading.Thread(
    target=emulator.run_emulator, args=(M64_LIB_PATH, M64_PLUGIN_PATH, M64_ROM_PATH)
)
thread1.start()
