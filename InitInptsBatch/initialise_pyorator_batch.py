# -------------------------------------------------------------------------------
# Name:        initialise_funcs.py
# Purpose:     script to read and write the setup and configuration files
# Author:      Mike Martin
# Created:     31/07/2020
# Licence:     <your licence>
# Description:#
#   Notes:
#       entries for drop-down menus are populated after GUI has been created and config file has been read
# ------------------------------------------------------------------------------- (exit)

__prog__ = 'initialise_pyorator_batch.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
from os.path import isfile, isdir, normpath, join, exists, lexists, split
from os import listdir, getcwd, makedirs
from calendar import month_abbr

from json import load as load_json, dump as dump_json
from json.decoder import JSONDecodeError

from time import sleep
import sys

from ora_excel_read_misc import identify_study_areas
from hwsd_bil import check_hwsd_integrity
from weather_datasets import read_weather_dsets_detail

from set_up_logging import set_up_logging
from ora_excel_read import (check_xls_run_file, check_params_excel_file, ReadStudy,
                            ReadCropOwNitrogenParms, ReadAnmlProdn)
from ora_cn_classes import CarbonChange, NitrogenChange, CropProdModel, LivestockModel, EconomicsModel
from ora_water_model import SoilWaterChange
from ora_lookup_df_fns import read_lookup_excel_file, fetch_display_names_from_metrics
from ora_gui_misc_fns import simulation_yrs_validate
from ora_wthr_misc_fns import read_csv_wthr_file, prod_system_to_descr

PROGRAM_ID = 'pyorator'
EXCEL_EXE_PATH = 'C:\\Program Files\\Microsoft Office\\root\\Office16'
NOTEPAD_EXE_PATH = 'C:\\Windows\\System32\\notepad.exe'

ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '
sleepTime = 5

MNTH_NAMES_SHORT = [mnth for mnth in month_abbr[1:]]

FNAME_ECON = 'PurchasesSalesLabour.xlsx'
FNAME_RUN = 'FarmWthrMgmt.xlsx'

def initiation(form):
    """
    this function is called to initiate the programme and process all settings
    """
    # retrieve settings
    # =================
    form.settings, form.lookup_df = _read_setup_file(PROGRAM_ID)

    # ORATOR parameters file
    # ======================
    parms_xls_fn = form.settings['params_xls']
    print('Reading: ' + parms_xls_fn)
    form.ora_parms = ReadCropOwNitrogenParms(parms_xls_fn)
    form.anml_prodn = ReadAnmlProdn(parms_xls_fn, form.ora_parms.crop_vars)

    # check weather data
    # ==================
    if form.settings['wthr_dir'] is None:
        form.wthr_sets = None
    else:
        form.wthr_sets = read_weather_dsets_detail(form)
        if len(form.wthr_sets) == 0:
            form.wthr_sets = None
    form.wthr_rsrces_gnrc = list(['CRU'])

    # initialise bridges across economics, livestock and carbon-nitrogen-water models
    # ===============================================================================
    form.all_runs_output = {}
    form.all_runs_crop_model = {}

    # Set flags to show if crop and livestock models have run
    # ===============================================================================
    form.crop_run = False
    form.livestock_run = False
    set_up_logging(form, PROGRAM_ID)

    return

def _read_setup_file(program_id):
    """
    read settings used for programme from the setup file, if it exists,
    or create setup file using default values if file does not exist
    """
    # validate setup file
    # ===================
    fname_setup = program_id + '_setup_batch.json'

    setup_file = join(getcwd(), fname_setup)
    if exists(setup_file):
        try:
            with open(setup_file, 'r') as fsetup:
                setup = load_json(fsetup)

        except (JSONDecodeError, OSError, IOError) as err:
            sleep(sleepTime)
            sys.exit(0)
    else:
        print(ERROR_STR + 'setup file ' + setup_file + ' must exist')
        sleep(sleepTime)
        sys.exit(0)

    # initialise vars
    # ===============
    settings = setup['setup']
    settings_list = ['config_dir', 'fname_png', 'log_dir', 'fname_lookup', 'study_area_dir', 'hwsd_dir',
                     'nsubareas', 'irrig_dflt', 'nrota_yrs_dflt', 'areas_dflt', 'excel_dir', 'wthr_dir', 'params_xls']
    for key in settings_list:
        if key not in settings:
            print(ERROR_STR + 'setting {} is required in setup file {} '.format(key, setup_file))
            sleep(sleepTime)
            sys.exit(0)

    print('Read setup file: {}\nLogs will be written to: {}'.format(setup_file, settings['log_dir']))

    # TODO: consider situation when user uses Apache OpenOffice
    # =========================================================
    excel_flag = False
    if isdir(settings['excel_dir']):
        excel_path = join(settings['excel_dir'], 'EXCEL.EXE')
        if isfile(excel_path):
            excel_flag = True
        else:
            print(ERROR_STR + 'Excel progam must exist - expected here: ' + excel_path)
    else:
        print(ERROR_STR + 'Excel directory must exist - usually here: ' + EXCEL_EXE_PATH)

    if not excel_flag:
        sleep(sleepTime)
        sys.exit(0)

    settings['excel_path'] = excel_path

    # validate mandatory lookup table Excel file
    # ==========================================
    lookup_df = read_lookup_excel_file(settings, batch_flag=True)
    if lookup_df is None:
        sleep(sleepTime)
        sys.exit(0)

    # validate mandatory parameters Excel file
    # ========================================
    params_xls = normpath(settings['params_xls'])
    file_desc = 'crop, OW, N and animal production parameters '
    print('Reading ' + file_desc + 'file')
    if check_params_excel_file(params_xls) is None:
        print(ERROR_STR + file_desc + params_xls + ' must exist')
        sleep(sleepTime)
        sys.exit(0)

    # validate mandatory economics Excel file
    # =======================================
    tmplt_dir = join(split(settings['log_dir'])[0], 'run', 'templates')
    econ_xls_fn = normpath(join(tmplt_dir, FNAME_ECON))
    if isfile(econ_xls_fn):
        print('Economics file: ' + econ_xls_fn)
    else:
        print(ERROR_STR + 'Economics file ' + econ_xls_fn + ' must exist')
        sleep(sleepTime)
        sys.exit(0)

    settings['econ_xls_fn'] = econ_xls_fn

    # used to display weather data
    # ============================
    notepad_path = NOTEPAD_EXE_PATH
    if isfile(notepad_path):
        settings['notepad_path'] = notepad_path
    else:
        print(WARN_STR + 'Could not find notepad exe file - usually here: ' + NOTEPAD_EXE_PATH)
        settings['notepad_path'] = None

    # make sure directories exist for weather, configuration and log files paths
    # ==========================================================================
    log_dir = settings['log_dir']
    if not lexists(log_dir):
        makedirs(log_dir)

    config_dir = settings['config_dir']
    if not lexists(config_dir):
        makedirs(config_dir)

    wthr_dir = settings['wthr_dir']
    if wthr_dir is not None:
        if lexists(wthr_dir):
            print('Weather datasets path: ' + wthr_dir)
        else:
            print(WARN_STR + ' weather datasets path ' + wthr_dir + ' does not exist')
            wthr_dir = None

    settings['wthr_dir'] = wthr_dir

    # validate study areas
    # ====================
    settings['fname_run'] = FNAME_RUN
    study_areas = identify_study_areas(None, settings['study_area_dir'], settings['fname_run'])

    if len(study_areas) == 0:
        print(ERROR_STR + 'No valid study areas in: ' + settings['study_area_dir'])
        sleep(sleepTime)
        sys.exit(0)

    studies = []
    for dirname in study_areas:
        dummy, study = split(dirname)
        studies.append(study)

    settings['studies'] = studies
    settings['farms'] = {}

    # only one configuration file for this application
    # ================================================
    config_file = normpath(settings['config_dir'] + '/' + program_id + '_config.json')
    settings['config_file'] = config_file
    print('Using configuration file: ' + config_file)

    # verify HWSD
    # ===========
    hwsd_dir = settings['hwsd_dir']
    if isdir(hwsd_dir):
        check_hwsd_integrity(hwsd_dir)
    else:
        print(ERROR_STR + 'HWSD not detected in ' + hwsd_dir)
        sleep(sleepTime)
        sys.exit(0)

    settings['inp_dir'] = ''  # this will be reset after valid Excel inputs file has been identified

    # only one configuration file for this application
    # ================================================
    config_file = normpath(settings['config_dir'] + '/' + program_id + '_config.json')
    settings['config_file'] = config_file

    settings['study'] = ''

    return settings, lookup_df

def read_config_file(form):
    """
    read widget settings used in the previous programme session from the config file, if it exists,
    or create config file using default settings if config file does not exist
    """
    USE_SWITCHES = list(['use_isda', 'use_csv', 'nyrs_ss', 'nyrs_fwd'])
    MANDAT_ATTRIBS = list(['mgmt_dir0', 'write_excel', 'clim_scnr_indx', 'strt_yr_ss_indx', 'strt_yr_fwd_indx',
                           'study', 'farm_name', 'use_exstng_soil']) + USE_SWITCHES
    EXTRA_ORG_WASTE = list(['owex_min', 'owex_max', 'ow_type_indx', 'mnth_appl_indx'])

    config_file = form.settings['config_file']
    if exists(config_file):
        try:
            with open(config_file, 'r') as fcnfg:
                config = load_json(fcnfg)
                print('Read config file ' + config_file)
        except (JSONDecodeError, OSError, IOError) as err:
            print(ERROR_STR + err)
            return False
    else:
        config = _write_default_config_file(config_file, form.settings['study_area_dir'])

    for attrib in MANDAT_ATTRIBS:
        if attrib not in config:
            if attrib == 'use_exstng_soil':
                config['use_exstng_soil'] = True
            else:
                print(ERROR_STR + 'attribute {} not present in configuration file: {}'.format(attrib, config_file))
                sleep(sleepTime)
                sys.exit(0)

    mgmt_dir0 = normpath(config['mgmt_dir0'])
    if not isdir(mgmt_dir0) or mgmt_dir0 == '.':
        # patch - select first study directory
        # ====================================
        study_dir = join(form.settings['study_area_dir'], config['study'])
        study_dirs = [dirnm for dirnm in listdir(study_dir) if isdir(join(study_dir, dirnm))]
        if len(study_dirs) > 0:
            mgmt_dir0 = join(study_dir, study_dirs[0])

    if not isdir(mgmt_dir0):
        mess = '\nManagement path: ' + mgmt_dir0 + ' does not exist\n\t- check configuration file ' + config_file
        print(ERROR_STR + mess)
        return False

    # check runfile
    # =============
    run_xls_fname = join(mgmt_dir0, FNAME_RUN)
    if isfile(run_xls_fname):
        run_fn_dscr, run_model_flag = check_xls_run_file(run_xls_fname, mgmt_dir0)
        print(run_fn_dscr)
    else:
        print(WARN_STR + '\nRun file ' + run_xls_fname + ' does not exist\n\t- select another management path')

    # =======================
    if config['write_excel']:
        form.settings['write_excel'] = True
        print('Will write comprehensive Excel output files')
    else:
        form.settings['write_excel'] = False

    # ================================
    print('Allowable organic waste types:')
    for ow_typ in form.ora_parms.ow_parms:
        if ow_typ != 'Organic waste type':
            print('\t' + ow_typ)

    # read the run file
    # =================
    study = ReadStudy(form, mgmt_dir0, run_xls_fname)
    if not study.study_ok_flag:
        return False

    mess = 'Use switches:\n'
    for use_switch in USE_SWITCHES:
        mess += '\t' + use_switch + ': ' +  str(config[use_switch])
    print(mess)

    mess = 'Numder of years for steady state run: ' +  str(config['strt_yr_ss_indx'])
    mess += '\tforward run: ' + str(config['strt_yr_fwd_indx'])
    print(mess)

    form.settings = dict(sorted(form.settings.items()))

    return True

def _write_default_config_file(config_file, study_area_dir):
    """

    """
    farm_name = 'Grassland'
    study = 'Dummy (IND)'
    _default_config = {
        'clim_scnr_indx': 0,
        'csv_wthr_fn': '',
        'farm_name': farm_name,
        'mgmt_dir0': join(study_area_dir, study, farm_name),
        'mnth_appl_indx': 4,
        'nyrs_fwd': 10,
        'nyrs_ss': 10,
        'ow_type_indx': 4,
        'owex_max': '10.0',
        'owex_min': '0.1',
        'strt_yr_fwd_indx': 0,
        'strt_yr_ss_indx': 0,
        'study': study,
        'use_csv': False,
        'use_isda': False,
        'write_excel': False
    }
    # if config file does not exist then create it...
    with open(config_file, 'w') as fconfig:
        dump_json(_default_config, fconfig, indent=2, sort_keys=True)
        return _default_config
