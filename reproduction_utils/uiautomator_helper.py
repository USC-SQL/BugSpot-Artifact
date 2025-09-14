import uiautomator2 as u2
from urllib3.exceptions import ReadTimeoutError
import cv2 as cv
import numpy as np
from os import makedirs
from os.path import dirname, abspath
import time

import sys
sys.path.append(dirname(abspath(__file__)))
from os_utils import dump_text_file, run_command
from logger_utils import get_logger
import re

logger = get_logger("uiautomator-helper")
def connect_uiautomator(emulator_id):
    d = u2.connect(emulator_id)
    print_device_info(d)
    return d

def print_device_info(d):
    logger.debug("Trying to connect to uiautomator")
    restart_times = 5
    while restart_times >= 0:
        try:
            # self.d.shell(['pm', 'install', '-r', '-t', '/data/local/tmp/app-uiautomator.apk'])
            logger.debug(f"Android emulator info: {d.info}")
            return
        except (OSError, u2.exceptions.GatewayError, u2.GatewayError) as e:
            logger.debug("Trying to reinit uiautomator")
            run_command("python -m uiautomator2 init", 60)
        restart_times -= 1
    logger.error("Unable to start UIAutomator...")
    raise Exception("ConnectionRefusedError: Unable to connect to UIAutomator")

def dump_snapshot(d, output_path):
    try:
        screenshot = d.screenshot(format='opencv')
        if screenshot is None:
            raise Exception
    except Exception or IOError or ReadTimeoutError as e:
        logger.error("Cannot dump screenshot. Generating a dummy picture..")
        w, h = d.window_size()
        screenshot = np.zeros((h, w), np.uint8)
        screenshot.fill(255)
    dir_name = dirname(output_path)
    makedirs(dir_name,exist_ok=True)
    cv.imwrite(output_path, screenshot)
    
def dump_view_hierarchy(d, output_path):
    retry_time = 10
    while retry_time > 0:
        time.sleep(1.5)
        try:
            vh = d.dump_hierarchy(pretty=True)
            break
        except Exception as e:
            logger.error("Cannot dump hierarchy. Trying reconnect again..")
            print_device_info(d)
            retry_time -= 1
    dump_text_file(output_path, vh)

def get_volume(d):
    adb_output = d.shell("dumpsys audio").output
    # Initialize variables to store the volumes
    stream_ring_volume = None
    stream_music_volume = None

    # Define the regex pattern to match the desired lines
    pattern_ring = r'- STREAM_RING:[\s\S]*?Current:\s*\d+\s*\(speaker\):\s*(\d+)'
    match_ring = re.search(pattern_ring, adb_output)
    if match_ring:
        stream_ring_volume = int(match_ring.group(1))

    pattern_music = r'- STREAM_MUSIC:[\s\S]*?Current:\s*\d+\s*\(speaker\):\s*(\d+)'
    match_music = re.search(pattern_music, adb_output)
    if match_music:
        stream_music_volume = int(match_music.group(1))

    return stream_ring_volume, stream_music_volume
    
def get_orientation(d)->str:
    """get the orientation of the device

    Args:
        

    Returns:
        str: could be "natural", "left", "right", "upsidedown"
    """
    return d.orientation
    
def get_log(d, clear_after_retrieve=True) -> str:
    log = d.shell("logcat -d").output
    if clear_after_retrieve:
        d.shell("logcat -c")
    return log
    

def audio_is_on(d, package_name)->bool:
    """get whether the audio of the mobile device is on

    Args:
        d (_type_): the uiautomator device object
        package_name (_type_): package name of the app under test

    Returns:
        bool: true means the audio is on
    """
    
    adb_output = d.shell("dumpsys media_session",timeout=10).output
    
    # Regex pattern to match the relevant information
    pattern = (
        r"package={package}.*state=PlaybackState {{state=(\d+),"
    ).format(package=re.escape(package_name))

    # Search for the pattern in the output
    match = re.search(pattern, adb_output, re.MULTILINE | re.DOTALL)

    if match:
        # Retrieve the state number from the match
        state_number = int(match.group(1))
        if state_number == 3:
            return True
    return False