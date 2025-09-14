
from os import makedirs
from shutil import copyfile
from recognizers.info_loader import RealTimeLoader, ManualInfoLoader, RoamInfoLoader
from reproduction_utils.os_utils import check_path_existence, dump_text_file, load_text_file
from report_parser.parser_main import llm_query
from recognizers.recognizer_main import dsl_inspector
from utils.cmd_args import CmdArgs
from reproduction_utils.logger_utils import get_logger
from os.path import join, exists
from utils.cmd_args import CmdArgs
import re
from utils.config import Config

logger = get_logger("main", CmdArgs.logger_level)

if CmdArgs.use_gpt_4:
    Config.llm_model = 'gpt-4-0613'
if CmdArgs.use_gpt_4_turbo:
    Config.llm_model = 'gpt-4-turbo-2024-04-09'
    
logger.info("Using LLM: " + Config.llm_model)

if CmdArgs.crawl_info:
    # under this mode, we only obtain the ui and device information
    loader = RealTimeLoader(CmdArgs.output_dir, CmdArgs.device_id, CmdArgs.app_pkg)
    loader.get_layout()
    loader.get_device_info()
    exit(0)

# dsl extraction
logger.info("Stage 1: Translating bug report text into DSL")
dsl_output_file = join(CmdArgs.output_dir, "dsl_desc.txt")
if CmdArgs.dsl_file_path is not None:
    logger.debug(f"Using provided DSL file {CmdArgs.dsl_file_path}.")
    check_path_existence(CmdArgs.dsl_file_path)
    makedirs(CmdArgs.output_dir, exist_ok=True)
    copyfile(CmdArgs.dsl_file_path, dsl_output_file)
if exists(dsl_output_file):
    dsl_description = load_text_file(dsl_output_file)
    logger.info("Reusing previous LLM output: "+dsl_description)
else:
    dsl_description = llm_query(CmdArgs.report_file)
    dump_text_file(join(CmdArgs.output_dir, "dsl_with_reasoning.txt"), dsl_description)
    if "Output:" in dsl_description:
        dsl_description = dsl_description.split("Output:")[1].strip()
    else:
        logger.error("The LLM response doesn't contain output.")
        exit(1)
    dump_text_file(dsl_output_file, dsl_description)

if CmdArgs.only_parse_dsl:
    exit(0)

# verification
logger.info("Stage 2: Verifying DSL on the app info")
info_loader = None
if CmdArgs.as_plugin:
    info_loader = RealTimeLoader(CmdArgs.output_dir, CmdArgs.device_id, CmdArgs.app_pkg)
elif CmdArgs.for_manual:
    info_loader = ManualInfoLoader(CmdArgs.reproduction_info, CmdArgs.app_pkg)
# else:
    # info_loader = RoamInfoLoader(CmdArgs.reproduction_info)
else:
    logger.error("Please specify either manual or plugin mode")
    exit(0)
    
reproduction_result = dsl_inspector(dsl_description, info_loader)
if reproduction_result:
   logger.info("Reproduction Results: Success") 
else:
   logger.info("Reproduction Results: Failure") 
    