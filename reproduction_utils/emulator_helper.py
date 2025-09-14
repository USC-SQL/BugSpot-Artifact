import logging
import os
import signal
import string
import sys
import time
import pathlib
from argparse import ArgumentParser
from os.path import join, basename, abspath, dirname
import socket
import random
# add the reproduction_utils dir to system path in order to find the other modules when running from other directory
sys.path.append(dirname(abspath(__file__)))
from logger_utils import get_logger
from os_utils import kill_process, run_command, kill_process_grp

emulator_ports = {
    "Android 4": 5554,
    "Android 5": 5556,
    "Android 6": 5558,
    "Android 7": 5560,
    "Android 8": 5562,
    "Android 9": 5564,
    "Android 10": 5566,
    "Android 11": 5568
}
emulator_names = {
    "Android 4": "Nexus6API19",
    "Android 5": "Nexus6API21",
    "Android 6": "Nexus6API23",
    "Android 7": "Nexus6API24",
    "Android 8": "Nexus6API26",
    "Android 9": "Nexus6API28",
    "Android 10": "Nexus6API29",
    "Android 11": "Nexus6API30"
}

api_to_android_version = {
    19: "Android 4",
    21: "Android 5",
    23: "Android 6",
    24: "Android 7",
    26: "Android 8",
    28: "Android 9",
    29: "Android 10",
    30: "Android 11",
}

android_version_to_api = {
    "Android 4": 19,
    "Android 5": 21,
    "Android 6": 23,
    "Android 7": 24,
    "Android 8": 26,
    "Android 9": 28,
    "Android 10": 29,
    "Android 11": 30
}


def parse_emulator_args(parser: ArgumentParser):
    parser.add_argument("-showEmulator", help="whether to show the UI of the emulator", default=False, action="store_true")
    parser.add_argument("--emulatorPort", help="the port for emulator, needs to be an even number", default=None, type=int)
    parser.add_argument("--emulatorWaitTime", help="the time limit to wait until the emulator starts", default=60, type=int)
    parser.add_argument("--emulatorMemorySize", help="the memory size for the emulator", default=None, type=int)
    parser.add_argument("--emulatorCores", help="the number of cores for the emulator to use", default=None, type=int)
    parser.add_argument("--emulatorPartitionSize", help="the partition size for emulator", default=None, type=int)
    parser.add_argument("-createNewEmulator", help="by using this flag, when starting emulator, the script will create new avd", default=False, action='store_true')
    parser.add_argument("--androidVersion", help="the version of android device to be started, format: 'Android X' X is an integer from 4 to 11",default=None)
    parser.add_argument("-showKeyboard", help="By specifying this flag, the emulator will be configured to show keyboard when starting",default=False, action="store_true")


def generate_random_string(length):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

class Emulator:
    emulator_proc = None
    cur_adb_port = None
    null_key_board_apk_file = join(pathlib.Path(__file__).parent.resolve(), "libs", "nullkeyboard.apk")
    acceleration_on = True
    create_new_emulator = False

    def __init__(self, android_version, show_window=False, port=None, emulator_start_wait_time=60, memory_size: int = None,
                 cores: int = None, partition_size: int = None, create_new_emulator=False, logger=None, clean_3rd_apps = True, show_keyboard = False):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGQUIT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self.logger = logger
        if self.logger is None:
            self.logger = get_logger('emulator')
        self.verbose = self.logger.level == logging.DEBUG

        self.logger.info("Starting Emulator...")
        self.check_hardware_acceleration()
        run_command("adb start-server", 10,verbose=self.verbose)
        try:
            self.create_new_emulator = create_new_emulator
            self.install_system_images(android_version)
            if self.create_new_emulator:
                emulator_start_wait_time = max(emulator_start_wait_time, 80)  # if create new emulator , the waiting time for starting avd is at least 80 seconds
                self.avd_name = None
                self.create_avd_device(android_version)
            else:
                self.avd_name = emulator_names[android_version]
                run_command(f"rm -f ~/.android/avd/{self.avd_name}.avd/*.lock", 10,verbose=self.verbose)
            window_option = '' if show_window else '-no-window'
            memory_size_option = f'-memory {memory_size}' if memory_size else ''
            cores_option = f'-cores {cores}' if cores else ''
            partition_size_option = f'-partition-size {partition_size}' if partition_size else ''
            acceleration_option = '-no-accel' if not self.acceleration_on else ''
            if port is None:
                self.cur_adb_port = emulator_ports[android_version]
            else:
                self.cur_adb_port = port
            self.check_port_validity(increase_step=10)
            self.emulator_proc = run_command(
                f"emulator -avd {self.avd_name} -port {self.cur_adb_port} {window_option} {memory_size_option} {cores_option} {partition_size_option} {acceleration_option}",verbose=self.verbose)
            if self.acceleration_on:
                time.sleep(emulator_start_wait_time)
            else:
                # if no accelation, wait longer time for emulator to be fully started.
                time.sleep(emulator_start_wait_time * 2)
            run_command(f"adb devices | grep {self.get_cur_emulator_id()}", 100,verbose=self.verbose)
            if clean_3rd_apps:
                run_command(f"adb -s emulator-{self.cur_adb_port} shell pm list packages -3 | cut -d':' -f2 | tr '\r' ' ' | xargs -r -n1 -t adb -s emulator-{self.cur_adb_port} uninstall", 100,verbose=self.verbose)
            self.logger.info(f"Emulator {self.avd_name} started on port {self.cur_adb_port}")
            if not show_keyboard:
                self.setup_null_keyboard()
        except Exception as e:
            # if any exception happend during starting the emulator, need to clear the started emulator and created avd
            self.__exit__(None, None, None)
            raise e

    def install_app(self, app_path):
        if self.cur_adb_port is None:
            raise Exception("Emulator is not started")
        run_command(f"adb -s emulator-{self.cur_adb_port} install -r {app_path}", 10,verbose=self.verbose)
        self.logger.info(f"{basename(app_path)} installed")

    def setup_null_keyboard(self):
        self.install_app(self.null_key_board_apk_file)
        run_command(f"adb -s emulator-{self.cur_adb_port} shell ime set com.wparam.nullkeyboard/.NullKeyboard", 10,verbose=self.verbose)
        self.logger.debug("Emulator is configured to hide keyboard.")

    def kill_emulator(self):
        if self.emulator_proc is not None:
            self.logger.debug(f"Trying to kill emulator with pid: {self.emulator_proc.pid} and name: {self.avd_name}")
            # kill_process(self.emulator_proc.pid, kill_children=True)
            try:
                run_command("ps aux | grep "+self.avd_name+" | awk '{print $2}' | xargs kill -9", time_limit=10, verbose=self.verbose)
            except Exception as e:
                self.logger.error(str(e))
            self.emulator_proc = None

    def get_cur_emulator_id(self):
        if self.cur_adb_port is not None:
            return f"emulator-{self.cur_adb_port}"
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kill_emulator()
        if self.create_new_emulator:
            self.delete_avd()
        self.logger.info("Cleaned up emulators")
    
    def _signal_handler(self, signal_received, frame):
        self.__exit__(None, None, None)
        sys.exit(0)

    def check_hardware_acceleration(self):
        try:
            run_command("emulator -accel-check",100,verbose=self.verbose)
            self.acceleration_on = True
            self.logger.debug("Hardware acceleration is available.")
        except Exception as e:
            self.logger.warning("Unable to use hardware acceleration for Android emulator. The emulator may run slowly.")
            self.acceleration_on = False

    def check_port_validity(self, increase_step):
        def __is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', int(port))) == 0
        while __is_port_in_use(self.cur_adb_port):
            self.cur_adb_port += increase_step

    def create_avd_device(self, android_version:str):
        self.logger.info("Creating AVD device")
        api_level = android_version_to_api[android_version]
        while True:
            self.avd_name = android_version.replace(" ", "") + generate_random_string(10)
            try:
                run_command(f'emulator -list-avds | grep {self.avd_name}', time_limit=10000,verbose=self.verbose)
            except Exception as e:
                # meaning that the above command failed to run, the device doesn't exist and the device name is valid
                break
        arch = self.check_system_arch()
        system_images = [f'system-images;android-{api_level};google_apis;{arch}', f'system-images;android-{api_level};default;{arch}']
        for system_image in system_images:
            try:
                run_command(f'avdmanager create avd -n "{self.avd_name}" -k "{system_image}" -d "Nexus 6"', time_limit=10000,verbose=self.verbose)
                self.logger.info(f"Created new avd on {android_version} named with {self.avd_name}")
                return
            except Exception as e:
                self.logger.info("Failed to create avd, try another system image")
                continue
        raise Exception(f"Failed to create avd on {android_version} named with {self.avd_name}")

    def install_system_images(self, android_version:str):
        self.logger.info("Installing system images")
        api_level = android_version_to_api[android_version]
        arch = self.check_system_arch()
        system_images = [f'system-images;android-{api_level};google_apis;{arch}', f'system-images;android-{api_level};default;{arch}']
        for system_image in system_images:
            try:
                run_command(f'sdkmanager "{system_image}"', time_limit=10000,verbose=self.verbose)
            except Exception as e:
                continue

    def check_system_arch(self):
        try:
            run_command(f'uname -p | grep x86', time_limit=100, verbose=self.verbose)
            return 'x86'
        except:
            return 'arm64-v8a'
        
    def delete_avd(self):
        try:
            self.logger.debug("Deleting created emulator")
            if self.avd_name is None:
                return
            run_command(
                f'avdmanager delete avd -n "{self.avd_name}"',
                time_limit=10000, verbose=self.verbose)
            self.logger.info(f"Deleted avd {self.avd_name}")
        except Exception as e:
            self.logger.error(str(e))
