## Automated Recognition of Buggy Behaviors from Mobile Bug Reports.
This repo contains source code for the technique introduced in paper "Automated Recognition of Buggy Behaviors from Mobile Bug Reports. (FSE 2025)"

The main functionality of the technique is to validate if the buggy behavior described in a bug report is triggered on the mobile device from a set of pre-collected information during the reproduction process.

### Environment Setup
1. Install Python 3.10.13.
2. Instal Python packages by running `pip install -r requirements.txt` and `python -m spacy download en_core_web_lg` under the current folder.
3. Get your GPT API key following [this webpage](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key) and set your key to environment variable `OPENAI_API_KEY`. 

### Running the tool
The tool takes four inputs:
- `--reportFile`: the path of a text file containing the bug report text  (See [example](./test_input/report.txt)).
- `--apkPath`: the path of the apk file for the target app (See [example](./test_input/app.apk)).
- `--outputDir`: the path of the output folder.
- `--reproductionInfo`: the path to the folder that contains the reproduction information collected during the automated reproduction process. Specifically, the folder should include three sub-folders: (1) "device_info" contains relevant system information (e.g., log, audio) (2) "screenshot" contains screenshot taken during executing reproduction UI actions, and (3) "view_hierarchy" contains view hierarchy files during executing UI actions. Note that, the files under each sub-folder is captured from the beginning state (before the first action), and after each UI action. See folder [Example Folder](./test_input/reproduction_info/) for detailed examples of the files.

Run the tool using the following command:
```bash
python $(pwd)/tool_main.py \
     --reportFile {REPORT_PATH} 
    --outputDir {OUTPUT_PATH} 
    --reproductionInfo {REPRODUCTION_INFO_FOLDER} 
    --apkPath {APK_PATH}
```
Replace the values in bracket with actual arguments. If no arguments are provided (run `python tool_main.py`), the tool is configured to use the example input files under folder [test_input](./test_input/), and generate output into [./output](./output/)

