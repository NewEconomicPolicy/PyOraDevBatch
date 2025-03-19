# -------------------------------------------------------------------------------
# Name:        initialise_funcs.py
# Purpose:     script to read read and write the setup and configuration files
# Author:      Mike Martin
# Created:     26/03/2020
# Licence:     <your licence>
# -------------------------------------------------------------------------------
#

__prog__ = 'initialise_funcs.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
from os.path import isfile, isdir, join, exists, split, normpath
from os import mkdir, getcwd

from json import dump as json_dump, load as json_load
from time import sleep
import sys

sleepTime = 5
STTNGS_MANDAT_ATTRIBS = list(['config_dir', 'fname_png', 'studies_dir', 'python_exe', 'sub_prog'])
ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '

def initiation(form):
    """
    this function is called to initiate the programme to process non-GUI settings.
    """

    # retrieve settings
    # ================
    setup_file = join(getcwd(), 'pyorator_sub_gui_setup.json')
    if not _read_setup_file(form, setup_file):
        print('Setup failed')
        sleep(sleepTime)
        sys.exit(0)

    form.settings['config_file'] = join(form.settings['config_dir'], 'pyorator_sub_gui_config.json')

    return

def _read_setup_file(form, setup_file):
    """
    # read settings used for programme from the setup file, if it exists,
    # or create setup file using default values if file does not exist
    """
    if exists(setup_file):
        try:
            with open(setup_file, 'r') as fsetup:
                setup = json_load(fsetup)
        except (OSError, IOError) as err:
                print(err)
                return False
    else:
        setup = _write_default_setup_file(setup_file)

    settings = setup['setup']

    for attrib in STTNGS_MANDAT_ATTRIBS:
        if attrib not in settings:
            print(ERROR_STR + 'attribute {} is required in setup file {} '.format(attrib, setup_file))
            sleep(sleepTime)
            sys.exit(0)

    mess = WARN_STR + 'Reading setup file ' + setup_file
    studies_dir = settings['studies_dir']
    if not isdir(studies_dir):
        print(mess + ' - studies dir: '+ studies_dir + ' is not a directory')

    fname_png = settings['fname_png']
    if not isfile(fname_png):
        print(mess + ' Could not find image file ' + fname_png)

    config_dir = settings['config_dir']
    if not isdir(config_dir):
        try:
            mkdir(config_dir)
        except (PermissionError, FileNotFoundError) as err:
            print(mess + ' Could not create configuration directory ' + config_dir)
            return False

    form.settings = settings

    return True

def read_config_file(form):
    """
    # read widget settings used in the previous programme session from the config file, if it exists,
    # or create config file using default settings if config file does not exist
    """
    config_file = form.settings['config_file']
    if exists(config_file):
        try:
            with open(config_file, 'r') as fconfig:
                config = json_load(fconfig)
        except (OSError, IOError) as err:         # does not catch all errors
            print(err)
            return False
    else:
        config = _write_default_config_file(config_file)

    if 'run_fn' in config:
        form.w_run_fn.setText(config['run_fn'])
    else:
        form.w_run_fn.setText('')

    return True

def write_config_file(form):
    """
    # write current selections to config file
    """
    config_file = form.settings['config_file']
    config = {'run_fn': normpath(form.w_run_fn.text())}

    with open(config_file, 'w') as fconfig:
        json_dump(config, fconfig, indent=2, sort_keys=True)

    mess = 'Updated ' + config_file
    print(mess)
    return

def _write_default_setup_file(setup_file):
    """
    #  stanza if setup_file needs to be created
    """
    orator_dir = getcwd()
    default_setup = {
        'setup': {
            'studies_dir': orator_dir,
            'fname_png': join(orator_dir + '\\images', 'orator_logo_small.png'),
            'config_dir' : orator_dir + '\\config'
        }
    }
    # create setup file
    # =================
    with open(setup_file, 'w') as fsetup:
        json_dump(default_setup, fsetup, indent=2, sort_keys=True)

    return default_setup
def _write_default_config_file(config_file):
    """
    """
    config_dir, dummy = split(config_file)
    if not isdir(config_dir):
        mkdir(config_dir)

    _default_config = {
         'fnames' : {
            'inp_fname' : '',
            'out_dir' : ''
         }
    }
    # if config file does not exist then create it...
    with open(config_file, 'w') as fconfig:
        json_dump(_default_config, fconfig, indent=2, sort_keys=True)
        return _default_config
