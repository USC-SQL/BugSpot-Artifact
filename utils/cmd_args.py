import argparse
import logging
from os.path import abspath, dirname, join
from pyaxmlparser import APK
from reproduction_utils.logger_utils import parse_logger_args

parser = argparse.ArgumentParser()
default_test_input_folder = join(dirname(dirname(abspath(__file__))), 'test_input')
parser.add_argument("--apkPath", help="path to the apk file", default=join(default_test_input_folder,"app.apk"))
parser.add_argument("--reproductionInfo", help="the directory used for storing the reproduction information", default=join(default_test_input_folder,"reproduction_info"))
parser.add_argument("--outputDir", help="the directory used to store output files", default="./output")
parser.add_argument("--deviceId",help="the device id of the target Android emulator", default="emulator-5554")
parser.add_argument("--reportFile", help="path to the bug report file to be analyzed", default=join(default_test_input_folder,"report.txt"))
parser.add_argument("-plugin",help="use the tool as a plugin when reproducing bug reports", default=False, action="store_true")
parser.add_argument("-manual",help="analyze the manual reproduction results", default=True, action="store_true")
parser.add_argument("-roam",help="analyze the roam's reproduction results", default=False, action="store_true")
parser.add_argument("-crawlInfo",help="obtain the UI and device state information", default=False, action="store_true")
parser.add_argument("-onlyDSLParsing",help="only run the DSL parsing state", default=False, action="store_true")
parser.add_argument("--dslFile", help="path to existing DSL file", default=None)
parser.add_argument("-useGPT4", help="use GPT-4 to do the task", default=True, action="store_true")
parser.add_argument("-useGPT4Turbo", help="use GPT-4 Turbo to do the task", default=False, action="store_true")


parse_logger_args(parser)

args = parser.parse_args()

class CmdArgs:
    apk_path = args.apkPath
    reproduction_info = args.reproductionInfo
    output_dir=args.outputDir
    report_file = args.reportFile
    device_id = args.deviceId
    as_plugin = args.plugin
    for_manual = args.manual
    for_roam = args.roam

    crawl_info = args.crawlInfo
    app_pkg = None

    logger_level=logging.DEBUG if args.verbose else logging.INFO
    
    only_parse_dsl = args.onlyDSLParsing
    dsl_file_path= args.dslFile
    
    use_gpt_4 = args.useGPT4
    use_gpt_4_turbo = args.useGPT4Turbo
    
CmdArgs.app_pkg = APK(CmdArgs.apk_path).package