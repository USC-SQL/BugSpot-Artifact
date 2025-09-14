import json
import multiprocessing
import os
import pickle
from shutil import rmtree
import signal
import subprocess
import psutil
from os import chdir, makedirs
from os.path import exists, dirname, abspath, isdir
import sys
import time
from typing import Dict, List
from pathlib import Path
# add the reproduction_utils dir to system path in order to find the other modules when running from other directory
sys.path.append(dirname(abspath(__file__)))
from logger_utils import get_logger
import datetime

logger = get_logger("os-utils")
cur_dir = os.getcwd()

def run_command(cmd_str, time_limit=None, verbose=True, running_dir = None):
    if running_dir is not None:
        chdir(running_dir)
    if verbose:
        logger.info(f"RUN CMD: {cmd_str}")
    p = None
    try:
        stdout_redirect = None
        if not verbose: # don't show the log output of subprocess when logger is configured to be INFO mode
            stdout_redirect = subprocess.DEVNULL
        p = subprocess.Popen("exec "+cmd_str, shell=True, stdout=stdout_redirect, stderr=subprocess.PIPE)
        std_error = ""
        if time_limit is not None:
            _, std_error = p.communicate(timeout=time_limit)
    except Exception as e:
        if p is not None:
            p.terminate()
        raise e
    finally: # note that, we cannot kill/clear the sub processes here, because sometime, we want to keep the subprocess to run in the background (e.g. the emulators);
        chdir(cur_dir)
    if p.returncode != 0 and p.returncode is not None:
        raise Exception(f"Command {cmd_str} failed to run: {std_error}")
    return p

def kill_process(proc_id, kill_children=False):
    try:
        parent = psutil.Process(proc_id)
        if kill_children:
            for child in parent.children(): 
                child.kill()
        parent.kill()
    except ProcessLookupError as e:
        pass
    except psutil.NoSuchProcess as e:
        pass
    
def kill_process_grp(proc_id):
    try:
        os.killpg(os.getpgid(proc_id), signal.SIGKILL)
    except ProcessLookupError as e:
        pass

def check_path_existence(path):
    if not exists(path):
        raise FileNotFoundError(f"{path} not found")


def load_pickle_file(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def load_json_file(step_file_path):
    with open(step_file_path, 'r') as f:
        return json.load(f)


def dump_json_file(step_file_path:str, json_obj:json):
    makedirs(dirname(step_file_path), exist_ok=True)
    with open(step_file_path, "w") as f:
        json.dump(json_obj, f, indent=4)


def dump_pickle_file(file_path, obj):
    makedirs(dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        pickle.dump(obj, f)


def load_text_file(file_path):
    with open(file_path, 'r') as f:
        return f.read().strip()


def dump_text_file(file_path, content):
    makedirs(dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        return f.write(content)
    
def append_text_to_file(file_path, content):
    with open(file_path, 'a') as f:
        f.write(content)

def clear_folder(path, create_if_not_exist=False):
    if not exists(path):
        if create_if_not_exist:
            makedirs(path)
        return
    if not isdir(path):
        return
    rmtree(path)
    makedirs(path)
    

def run_parallel(func, args_list:List[List], kwargs_list:List[Dict]=None, processes=4, delay=1):
    """
    Runs the specified function in parallel on the specified arguments and keyword arguments.

    Parameters:
        func (function): The function to run in parallel.
        args_list (list): A list of argument lists to pass to the each function call.
        kwargs_list (list, optional): A list of dictionary containing keyword arguments to pass to the each function call. Defaults to None.
        processes: A number specifying how many processes to use.
    Returns:
        list: A list of the return values from each call to the function.
    """
    logger.info(f'Running function: {func.__name__} in parallel (Max {processes} threads. In total {len(args_list)} threads.)')
    results = []
    
    # Create a pool of worker processes
    with multiprocessing.Pool(processes=processes) as pool:
        # Call the target function on each set of arguments in parallel
        if kwargs_list is None:
            kwargs_list = [{}] * len(args_list)
        for args, kwargs in zip(args_list, kwargs_list):
            result = pool.apply_async(func, args=args, kwds=kwargs)
            results.append(result)
            time.sleep(delay)

        # Monitor the progress of the computation
        total_tasks = len(results)
        number_ready = -1
        while number_ready!=total_tasks:
            new_ready = sum([1 for result in results if result.ready()])
            if new_ready != number_ready:
                number_ready = new_ready
                print(f"Finished {number_ready}/{total_tasks} tasks ...")
            # Sleep for a short while to avoid printing too frequently

    try:
        # Return the combined results
        return [r.get() for r in results]
    except multiprocessing.pool.MaybeEncodingError as e:
        pass

def read_file_as_string(file_path):
    with open(file_path, "r") as f:
        return f.read().replace(" ","").replace("\n","").strip()


def list_files_in_order(dir_name, sort_key=None, reverse = False):
    """
    List all files in their full path under a directory with certain order
    :param dir_name: the directory name to search
    :param sort_key: the key used for sorting the file names; use False if you don't want the files to be sorted
    """
    files = []
    for root, _, filenames in os.walk(dir_name):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            files.append(full_path)
    if sort_key is not False:
        files.sort(key=sort_key, reverse= reverse)
    return files
    

def get_current_time_stamp():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def get_file_name(file_path):
    return Path(file_path).stem