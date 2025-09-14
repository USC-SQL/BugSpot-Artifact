import sys
from os.path import dirname, abspath, join
sys.path.append(dirname(abspath(__file__)))
sys.path.append(dirname(dirname(abspath(__file__))))
import re
from info_loader import InfoLoader, ManualInfoLoader
from reproduction_utils.logger_utils import get_logger
from reproduction_utils.os_utils import load_text_file
from dsl import *
import ast
from utils.cmd_args import CmdArgs

logger = get_logger("recognizer_main", CmdArgs.logger_level)

# constants
def_regex = "(\w+)\s*=\s*(\w+)\((.*)\)"

def dsl_inspector(dsl_str:str, info_loader:InfoLoader) -> bool:
    """
    Check whether the bug described in DSL has been reproduced successfully
    """
    parts = dsl_str.split("AND")
    vars = [p for p in parts if re.search(def_regex, p) is not None]
    ops = [p for p in parts if re.search(def_regex, p) is None]

    for d in vars:
        match = re.search(def_regex, d)
        if match:
            v_name = match.group(1)
            class_name = match.group(2)
            arguments_str = match.group(3)

            # Manually convert arguments_str into a valid dictionary string
            arguments_str = "{" + arguments_str + "}"
            # arguments_str = re.sub(r'(log|is_crash)=', r'"\1":', arguments_str)
            arguments = ast.literal_eval(arguments_str)

            tmp_obj = globals()[class_name](**arguments)
            locals()[v_name] = tmp_obj

            if isinstance(tmp_obj, D) or isinstance(tmp_obj, S):
                # instantiating a Device or a Screen object, need to validate them immediately
                retrieve_prev_info = v_name.endswith("1") # s1 or d1 represent the previous screen / state
                tmp_obj.populate_info(info_loader, retrieve_prev_info)
                logger.debug("Initialized "+str(tmp_obj))
                if not tmp_obj.validate():
                    logger.info(f"{d} is not satisfiable")
                    return False
        else:
            logger.error("Cannot parse def expression: "+d)
    
    def __op_order__(op_str):
        # give inScreen operator a higher priority, to make sure we locate the widgets first and populate its information before processing the other ops
        if "in_screen" in op_str:
            return 1
        return 2
    
    ops.sort(key=__op_order__)

    satisfiable = True
    for op in ops:
        if not eval(op):
            satisfiable = False
            logger.info(f"{op} is unsatisfiable.")
    if satisfiable:
        logger.info(f"{dsl_str} is satisfiable.")
    return satisfiable