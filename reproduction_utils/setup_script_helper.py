from os.path import join, abspath, dirname
import sys
sys.path.append(dirname(abspath(__file__)))
from os_utils import check_path_existence


class SetupScriptHelper:

    def __init__(self, setup_script_path):
        self.setup_script_path = setup_script_path
        self.java_setup_script_root = join(setup_script_path, "SetupApk")
        self.python_setup_script_root = join(setup_script_path, "SetupScripts")

    def get_java_setup_script_file(self, app_id):
        setup_file_id = app_id.replace("-","_")
        file_path = join(self.java_setup_script_root, f"app/src/androidTest/java/com/reprobot/setup/{setup_file_id}_run.java")
        check_path_existence(file_path)
        return file_path

    def get_python_setup_script_file(self, app_id):
        setup_file_id = app_id.replace("-","_")
        file_path = join(self.python_setup_script_root, f"{setup_file_id}_run.py")
        check_path_existence(file_path)
        return file_path
