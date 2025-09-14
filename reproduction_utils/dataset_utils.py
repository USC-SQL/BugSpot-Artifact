import sys
from os import listdir
from os.path import join, exists, abspath, dirname

from pyaxmlparser import APK
import re

# add the reproduction_utils dir to system path in order to find the other modules when running from other directory
sys.path.append(dirname(abspath(__file__)))
from os_utils import check_path_existence


class DatasetUtils:
    dataset_dir = None

    def __init__(self, dataset_dir):
        self.dataset_dir = dataset_dir
        self.bug_report_dir = join(dataset_dir, "bug_reports")
        self.apk_dir = join(dataset_dir, "signed_apks")
        self.s2r_gt_dir= join(dataset_dir, "ground_truth")
        self.match_gt_dir= join(dataset_dir, "match_ground_truth")
        self.error_msg_dir= join(dataset_dir, "oracle")
        self.reproduce_info_dir= join(dataset_dir, "reproduction_info")
        self.dsl_gt_dir = join(dataset_dir, "dsl_oracle_ground_truth")
        check_path_existence(self.dataset_dir)
        check_path_existence(self.bug_report_dir)
        check_path_existence(self.apk_dir)
        check_path_existence(self.s2r_gt_dir)
        check_path_existence(self.match_gt_dir)
        check_path_existence(self.error_msg_dir)
        check_path_existence(self.reproduce_info_dir)
        check_path_existence(self.dsl_gt_dir)
        self.AUTs = None

    def retrieve_all_app_ids(self):
        if self.AUTs is None:
            self.AUTs = {}
            for android_version in listdir(self.bug_report_dir):
                apk_ids = [re.sub(r"(\.txt|-full\.txt)", "", i) for i in listdir(join(self.bug_report_dir, android_version)) if
                           i.endswith(".txt")]
                self.AUTs[android_version] = apk_ids
        return self.AUTs

    def get_apk_path(self, app_id):
        apk_path = join(self.apk_dir, app_id + ".apk")
        if exists(apk_path):
            return apk_path
        else:
            raise FileNotFoundError(f"There is no {app_id}.apk")

    def get_error_msg_file_path(self, app_id):
        err_msg_file = join(self.error_msg_dir, app_id+".txt")
        check_path_existence(err_msg_file)
        return err_msg_file

    def get_bug_report_path(self, app_id):
        bug_report_path = join(self.bug_report_dir, self.get_android_version(app_id), app_id + ".txt")
        check_path_existence(bug_report_path)
        return f"\"{bug_report_path}\""
    
    def get_full_bug_report_path(self, app_id):
        bug_report_path = join(self.bug_report_dir, self.get_android_version(app_id), app_id + "-full.txt")
        check_path_existence(bug_report_path)
        return f"\"{bug_report_path}\""

    def get_android_version(self, app_id):
        AUTs = self.retrieve_all_app_ids()
        for android_version in AUTs:
            if app_id in AUTs[android_version]:
                return android_version
        self.__raise_no_app_exception(app_id)

    def get_android_api_level(self, app_id):
        android_version = self.get_android_version(app_id)
        android_version_to_api_level = {
            "Android 4": 19,
            "Android 5": 21,
            "Android 6": 23,
            "Android 7": 24,
            "Android 8": 26,
            "Android 9": 28,
            "Android 10": 29,
            "Android 11": 30,
        }
        return android_version_to_api_level[android_version]

    def __raise_no_app_exception(self, app_id):
        raise FileNotFoundError(f"There is no {app_id}.apk")

    def get_apk_pkg(self, app_id):
        apk_path = self.get_apk_path(app_id)
        return APK(apk_path).package

    def get_s2r_gt_path(self, app_id):
        s2r_gt_path = join(self.s2r_gt_dir, app_id+".json")
        check_path_existence(s2r_gt_path)
        return s2r_gt_path

    def get_match_gt_path(self, app_id):
        match_gt_path = join(self.match_gt_dir, app_id+".json")
        check_path_existence(match_gt_path)
        return match_gt_path

    def get_reproduction_info_path(self, app_id):
        repro_info_path = join(self.reproduce_info_dir, app_id)
        check_path_existence(repro_info_path)
        return repro_info_path

    def get_dsl_ground_truth_path(self, app_id):
        dsl_gt_path = join(self.dsl_gt_dir, app_id+".txt")
        check_path_existence(dsl_gt_path)
        return dsl_gt_path