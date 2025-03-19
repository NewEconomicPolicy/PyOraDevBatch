#-------------------------------------------------------------------------------
# Name:        PyOratorSubGUI.py
# Purpose:     GUI to perform batch jon submisssions
# Author:      Mike Martin
# Created:     26/03/2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------

__prog__ = 'PyOratorSubGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import sys
from os.path import normpath, split, join

from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel,
                                                            QPushButton, QApplication, QFileDialog)
from subprocess import Popen, PIPE, STDOUT

from initialise_sub_funcs import read_config_file, initiation, write_config_file

WDGT_SIZE_110 = 110

class Form(QWidget):
    '''
    define two vertical boxes, in LH vertical box put the painter and in RH put the grid
    define main horizon box to put LH and RH vertical boxes in
    grid layout consists of combo boxes, labels and buttons
    '''
    def __init__(self, parent=None):

        super(Form, self).__init__(parent)

        initiation(self)
        font = QFont(self.font())
        font.setPointSize(font.pointSize() + 1)
        self.setFont(font)

        # define two vertical boxes, in LH vertical box put the painter and in RH put the grid
        # define horizon box to put LH and RH vertical boxes in
        hbox = QHBoxLayout()
        hbox.setSpacing(10)

        # left hand vertical box consists of png image
        # ============================================
        lh_vbox = QVBoxLayout()

        # LH vertical box contains image only
        w_lbl20 = QLabel()
        pixmap = QPixmap(self.settings['fname_png'])
        w_lbl20.setPixmap(pixmap)

        lh_vbox.addWidget(w_lbl20)

        # add LH vertical box to horizontal box
        hbox.addLayout(lh_vbox)

        # right hand box consists of combo boxes, labels and buttons
        # ==========================================================
        rh_vbox = QVBoxLayout()

        # The layout is done with the QGridLayout
        grid = QGridLayout()
        grid.setSpacing(10)  # set spacing between widgets

        # ========== spacer
        irow = 1
        grid.addWidget(QLabel(' '), irow, 0)

        # =================
        irow += 1
        w_run_pb = QPushButton('Select PyOrator run file:')
        helpText = 'PyOrator run file'
        w_run_pb.setToolTip(helpText)
        grid.addWidget(w_run_pb, irow, 0)
        w_run_pb.clicked.connect(self.fetchRunFile)

        w_run_fn = QLabel('x' * 10)
        # w_run_fn.resize(1600, 20)
        grid.addWidget(w_run_fn, irow, 1, 1, 5)
        self.w_run_fn = w_run_fn

        # ========== spacer
        irow += 1
        grid.addWidget(QLabel(' '), irow, 0)

        # ==================== operations ======================
        irow += 1
        w_sub_job = QPushButton('Submit batch job')
        helpText = 'Submit batch job'
        w_sub_job.setToolTip(helpText)
        w_sub_job.setFixedWidth(WDGT_SIZE_110)
        w_sub_job.clicked.connect(self.subBatchJob)
        grid.addWidget(w_sub_job, irow, 0)

        # ==================
        w_exit = QPushButton('Exit', self)
        grid.addWidget(w_exit, irow, 6)
        w_exit.clicked.connect(self.exitClicked)

        # ==================
        # add grid to RH vertical box
        rh_vbox.addLayout(grid)

        # vertical box goes into horizontal box
        hbox.addLayout(rh_vbox)

        # the horizontal box fits inside the window
        self.setLayout(hbox)

        # posx, posy, width, height
        # =========================
        self.setGeometry(300, 300, 600, 250)
        self.setWindowTitle('Submit PyOrator batch job')

        # reads and set values from last run
        # ==================================
        read_config_file(self)

    def subBatchJob(self):
        """
        run the make simulations script
        """
        run_fn = normpath(self.w_run_fn.text())
        run_dir = split(run_fn)[0]
        self.settings['run_dir'] = run_dir

        cmd_str = self.settings['python_exe'] + ' ' + self.settings['sub_prog'] + ' "' + self.settings['run_dir'] + '"'
        new_inst = Popen(cmd_str, shell=False, stdin=PIPE, stderr=STDOUT)

    def fetchRunFile(self):
        """
        C
        """
        fname_cur = self.w_run_fn.text()
        fname, dummy = QFileDialog.getOpenFileName(self, 'Use file', fname_cur, 'Excel files (*.xlsx)')
        if fname != '' and fname != fname_cur:
            fname = normpath(fname)
            self.w_run_fn.setText(fname)

    def exitClicked(self):
        '''
        write last GUI selections
        '''
        write_config_file(self)
        self.close()

def main():
    """
    """
    app = QApplication(sys.argv)  # create QApplication object
    form = Form() # instantiate form
    # display the GUI and start the event loop if we're not running batch mode
    form.show()             # paint form
    sys.exit(app.exec_())   # start event loop

if __name__ == '__main__':
    main()
