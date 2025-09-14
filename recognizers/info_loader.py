import sys
from os.path import dirname, abspath, join, basename
import re
sys.path.append(dirname(dirname(abspath(__file__))))
from reproduction_utils.uiautomator_helper import audio_is_on, connect_uiautomator, dump_snapshot, dump_view_hierarchy, get_log, get_orientation, get_volume
from reproduction_utils.logger_utils import get_logger
from reproduction_utils.os_utils import dump_json_file, get_current_time_stamp, get_file_name, list_files_in_order, load_json_file, load_text_file
from reproduction_utils.layout_utils import Layout
from utils.cmd_args import CmdArgs

logger = get_logger("info-loader", CmdArgs.logger_level)

class DeviceInfo:
    """
    A class stores the basic information of the device
    """
    def __init__(self) -> None:
        self.log = ""
        self.volume = None
        self.audio = None
        self.orientation = None
        self.id = None
    
    def from_json(self, device_info_file):
        info_json = load_json_file(device_info_file)
        self.log = info_json['log']
        self.volume = info_json['volume']
        self.audio = info_json['audio']
        self.orientation = info_json['orientation']
        self.id = get_file_name(device_info_file)

    def to_json(self):
        return {
            "volume":self.volume,
            "audio": self.audio,
            "log": self.log,
            "orientation": self.orientation,
        }
        
    def set_log(self, log_txt):
        self.log = log_txt

    def set_volume(self, volume):
        self.volume = volume

    def set_audio(self, audio):
        self.log = audio 

    def set_orientation(self, orientation):
        self.orientation = orientation 
    
def select_file(files, second_last, is_reversed=False) -> str:
    last_index = 0 if is_reversed else -1
    second_last_index = 1 if is_reversed else -2
    if second_last:
        if len(files)>1:
            file_path = files[second_last_index]
        else:
            raise Exception("Don't have enough layout files to retrieve")
    else:
        if len(files)>0:
            file_path = files[last_index]
        else:
            raise Exception("Don't have enough layout files to retrieve") 
    return file_path

class InfoLoader():
    """
    Class for loading real-time information for checking reproduction result
    """
    def __init__(self, app_pkg) -> None:
        self.app_pkg = app_pkg
    
    def get_layout(self, second_last = False):
        raise NotImplementedError("Parent method. Should not be invoked!")

    def get_device_info(self, second_last = False)->DeviceInfo:
        raise NotImplementedError("Parent method. Should not be invoked!")
        
class RealTimeLoader(InfoLoader):
    def __init__(self, output_path, device_id, app_pkg) -> None:
        super().__init__(app_pkg)
        self.output_path = output_path
        self.d = connect_uiautomator(device_id)

    def get_layout(self, second_last = False):
        # retrieve real-time info from device
        logger.info("Retrieving the current UI state...")
        file_name = get_current_time_stamp()
        dump_view_hierarchy(self.d, join(self.output_path, "view_hierarchy",file_name+".xml"))
        dump_snapshot(self.d, join(self.output_path, "screenshot",file_name+".png"))
        
        # select real-time info
        layout_files = list_files_in_order(join(self.output_path,"view_hierarchy"))
        file_path = select_file(layout_files, second_last)
        logger.info("Done...")
        return Layout(file_path, get_file_name(file_path))


    def get_device_info(self, second_last = False) -> DeviceInfo:
        # retrieve real-time info from device
        logger.info("Retrieving the current device state...")
        file_name = "info_"+get_current_time_stamp()+".json"
        device_info = DeviceInfo()
        
        device_info.audio = "on" if audio_is_on(self.d, self.app_pkg) else "off"
        device_info.log = get_log(self.d)
        device_info.volume = get_volume(self.d)[0]
        device_info.orientation = get_orientation(self.d)
        
        # save real-time info
        dump_json_file(join(self.output_path, "device_info", file_name),device_info.to_json())
             
        # select real-time info
        state_files = list_files_in_order(join(self.output_path,"device_info"))

        file_path = select_file(state_files, second_last)
        state = DeviceInfo()
        state.from_json(file_path)
        logger.info("Done...")
        return state 
        
class RoamInfoLoader(InfoLoader):
    """
    Instantiation for collecting outputs from ROAM
    """
    def __init__(self, output_path) -> None:
        raise NotImplementedError()
        self.output_path = output_path
        
    def get_layout(self, second_last = False):
        """
        Get the layout of the last UI screen.

        :param second_last: if it's true, get the second last one.
        """
        
        files = list_files_in_order(
            join(self.output_path, "reproduction_result","screenshots"), 
            sort_key=lambda x: [int(num) for num in basename(x).strip(".xml").split("_")[1::2]] if x.endswith(".xml") else [-1],
            reverse=True
        )
        
        file_path = select_file(files, second_last, True)
        return Layout(file_path, get_file_name(file_path))
            
    def get_device_info(self, second_last=False) -> DeviceInfo:
        """
        Load device info from existing outputs of ROAM. As Roam only dumped the logcat info, only log is loaded.
        """
        log_files = list_files_in_order(
            join(self.output_path, "reproduction_result","screenshots"), 
            sort_key=lambda x: [int(num) for num in basename(x).strip(".txt").split("_")[2::2]] if basename(x).startswith("logcat") else [-1],
            reverse=True
        )
        log_file = select_file(log_files, second_last, True)
        device_info = DeviceInfo()
        device_info.set_log(load_text_file(log_file))
        return device_info
        
class ManualInfoLoader(InfoLoader):
    def __init__(self, output_path, app_package) -> None:
        super().__init__(app_package)
        self.output_path = output_path
    
    def get_layout(self, second_last = False):
        layout_files = list_files_in_order(join(self.output_path,"view_hierarchy"))
        file_path = select_file(layout_files, second_last)
        return Layout(file_path, get_file_name(file_path))

    def get_device_info(self, second_last = False) -> DeviceInfo:
        state_files = list_files_in_order(join(self.output_path,"device_info"))

        file_path = select_file(state_files, second_last)
        state = DeviceInfo()
        state.from_json(file_path)
        logger.info("Done...")
        return state 
            
