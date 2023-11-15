"""
This script performs checks on generated files and reports for different generators based on workflow parameters.

The `_generator_is` variable is a dictionary with keys and values indicating information about the workflow being run.
Values for each key are determined by how this script is called by the .yml files in .github/workflows.

The `cryo_library` variable is used to determine which library (sky130hd_cryo, sky130hs_cryo, sky130hvl_cryo) the workflow is targeting.

1. DRC and LVS Filename Declaration:
   This section declares possible DRC and LVS filenames for different generators. 
   The first condition checks for sky130hd_temp and sky130hvl_ldo, while the elif condition checks for various cryo libraries.

2. DRC Check:
   - Checks if the content in the generated DRC report file matches the template DRC report file stored in .github/scripts/expected_drc_reports/.
   - If the number of lines in the DRC report files for temp-sense-gen and cryo-gen is greater than 3, it indicates non-zero errors in the make process.

3. LVS Check:
   - Checks if the LVS report generated by the cryo-gen make has the word 'failed' in the last line, raising an error if found.
   - Conducts a search for the word 'failed' in the LVS reports for ldo-gen and temp-sense-gen, raising a ValueError if found.

4. Result File Check:
   - Calls the check_gen_files() function from generators/common/check_gen_files.py.
   - Checks if various files (.v, .sdc, .cdl, .sp, .spice, etc.) have been generated for the required generators.
   - Takes input parameters: the test.json filename, the dictionary of possible generators, and the cryo_library.
"""

import sys
import json
import os
import re, subprocess
from common.get_ngspice_version import get_ngspice_version
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common.check_gen_files import check_gen_files

sys.stdout.flush()

cryo_library = ""
_generator_is = {
    'sky130hvl_ldo': 0, 
    'sky130hd_temp': 0, 
    'sky130XX_cryo': 0
}

if len(sys.argv) == 1:
    _generator_is['sky130hd_temp'] = 1
elif len(sys.argv) > 1:
    if sys.argv[1] == 'sky130hvl_ldo':
        _generator_is['sky130hvl_ldo'] = 1
    else:
        _generator_is['sky130XX_cryo'] = 1

if _generator_is['sky130XX_cryo']:
    # check which cryo-gen library's workflow is being run
    dir_path = r'flow/reports'
    lib = os.listdir(dir_path)
    cryo_library = str(lib[0])

## DRC and LVS Filename Declaration 
if _generator_is['sky130hd_temp'] or _generator_is['sky130hvl_ldo']:
    drc_filename = "work/6_final_drc.rpt"
    lvs_filename = "work/6_final_lvs.rpt"
elif len(sys.argv) > 1 and sys.argv[1] == cryo_library:
    drc_filename = "flow/reports/" + sys.argv[1] + "/cryo/6_final_drc.rpt"
    lvs_filename = "flow/reports/" + sys.argv[1] + "/cryo/6_final_lvs.rpt"


## DRC check 
if _generator_is['sky130hvl_ldo']:
    expected_ldo_rpt_filename = "../../../.github/scripts/expected_drc_reports/expected_ldo_drc.rpt"
    with open(drc_filename) as f1, open(expected_ldo_rpt_filename) as f2:
        content1 = f1.readlines()
        content2 = f2.readlines()
        if content1 == content2:
            print("DRC is clean!")
        else:
            raise ValueError("DRC failed!")
elif sum(1 for line in open(drc_filename)) > 3:
    raise ValueError("DRC failed!")
else:
    print("DRC is clean!")


##  LVS Check
if len(sys.argv) > 1 and sys.argv[1] == cryo_library:    
    lvs_line = subprocess.check_output(["tail", "-1", lvs_filename]).decode(
        sys.stdout.encoding
    )
    regex = r"failed"
    match = re.search(regex, lvs_line)
    
    if match != None:
        raise ValueError("LVS failed!")
    else:
        print("LVS is clean!")
else:
    with open(lvs_filename) as f:
        f1 = f.read()
    
        if "failed" in f1:
            raise ValueError("LVS failed!")
        else:
            print("LVS is clean!")

## Result File Check
if _generator_is['sky130hvl_ldo']:
   json_filename = "spec.json"
else:
   json_filename = "test.json"

if check_gen_files(json_filename, _generator_is, cryo_library):
        print("Flow check is clean!")
else:
    print("Flow check failed!")

if len(sys.argv) == 1:
    prev_ngspice_ver = 41
    installed_ngspice_ver = get_ngspice_version()
    sim_state_filename = "work/sim_state_file.txt"

    if installed_ngspice_ver != 0:
        if installed_ngspice_ver == prev_ngspice_ver:
            result_filename = "work/prePEX_sim_result" 

            with open(result_filename) as f2, open("../../../.github/scripts/expected_sim_outputs/prePEX_sim_result.txt") as f1:
                content1 = f2.readlines()
                content2 = f1.readlines()
                if content1 != content2:
                    raise ValueError("Simulations failed: simulation result file does not match!")
        else:
            print("Warning: the ngspice version does not match, "
                          "frequency results might not match! "
                          "Please contact a maintainer of the repo.")

    sim_state = json.load(open("work/sim_state_file.txt"))
    if sim_state["failed_sims"] != 0:
        raise ValueError("Simulations failed: Non zero failed simulations!")

    for folder_num in range(1, sim_state["completed_sims"] + 1):
        dir_path = r'simulations/run/'
        pex_path = os.listdir(dir_path)

        file_name = "simulations/run/" + pex_path + "/" + str(folder_num) + "/"
        param_file = file_name + "parameters.txt"
        log_file = file_name + "sim_" + str(folder_num) + ".log"
        spice_file = file_name + "sim_" + str(folder_num) + ".sp"

        if os.path.exists(log_file) and os.path.exists(log_file) and os.path.exists(spice_file):
            pass
        else:
            raise ValueError("Simulations failed: required of run folders do not exist!")

    print("Simulations are clean!")