import sys
from os.path import dirname, abspath, join
sys.path.append(dirname(dirname(abspath(__file__))))
from reproduction_utils.os_utils import load_text_file
from reproduction_utils.llm_helper import language_query
from reproduction_utils.logger_utils import get_logger
from utils.cmd_args import CmdArgs
from utils.config import Config

logger = get_logger("parser-main", CmdArgs.logger_level)

def load_prompts(example_ids):
    prompt_text = ""

    for i in example_ids:
        prompt_text += "\n\n"
        prompt_text += load_text_file(join(dirname(abspath(__file__)), "prompts", i+".txt"))
     
    return prompt_text


def llm_query(bug_report_path):
    system_prompt = load_prompts(
        [
            'system_msg', 
            'dummy_1', # crash with error message
            'dummy_2', # crash with no error message
            'nextcloud_notes_android_1914', # Display single element with text desc, in Steps; Device log
            'libre_tube_LibreTube_594', # Display single element with desc and location, in Actual Behavior
            'celzero_rethink_app_403', # Display two elements with status, desc
            'flex3r_DankChar_66', # keyboard on
            'tachiyomiorg_tachiyomi_3567', # Two screens remain the same
            'RetroMusicPlayer_RetroMusicPlayer_1412', # Two screens, element dissappear
            "jacese-screen-324", # Display element
            "audio",
            "language",
            "text-display"
        ]
    )
    report_text = load_text_file(bug_report_path)
    logger.info("Bug report:\n"+report_text)

    response, model_info = language_query("Input:\n"+report_text, system_prompt, model=Config.llm_model, seed=Config.llm_seed, temperature=Config.llm_temperature)

    logger.info(response)
    return response


if __name__ == "__main__":
    bug_report_file = join(dirname(dirname(__file__)),"test_input","report-recdroid-13.txt")
    response = llm_query(bug_report_file)
    print(response)