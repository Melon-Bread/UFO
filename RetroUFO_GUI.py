#!/usr/bin/env python3
"""
Grabs the latest version of every libretro core from the build bot.
"""

__author__ = "Melon Bread"
__version__ = "0.8.0"
__license__ = "MIT"

import argparse
import os
import platform
import sys
import zipfile
from pathlib import Path
from shutil import rmtree
from urllib.request import urlretrieve
from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QComboBox, QCheckBox, QPushButton, QFileDialog, \
    QVBoxLayout, QTextEdit


URL = 'https://buildbot.libretro.com/nightly'

# These are the default core locations with normal RetroArch installs based off of 'retroarch.default.cfg`
CORE_LOCATION = {
    'linux': '{}/.config/retroarch/cores'.format(Path.home()),
    'windows': '{}/AppData/Roaming/RetroArch/cores'.format(Path.home())
}

class Form(QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setWindowTitle('RetroUFO')

        # Create widgets
        self.chkboxPlatformDetect = QCheckBox('Platform Auto-Detect')
        self.chkboxPlatformDetect.setChecked(True)
        self.chkboxPlatformDetect.stateChanged.connect(self.auto_platform)

        self.cmbboxPlatform = QComboBox()
        self.cmbboxPlatform.setEnabled(False)
        self.cmbboxPlatform.setEditable(False)
        self.cmbboxPlatform.addItem('Linux')
        self.cmbboxPlatform.addItem('Windows')

        self.chkboxLocationDetect = QCheckBox('Core Location Auto-Detect')
        self.chkboxLocationDetect.setChecked(True)
        self.chkboxLocationDetect.stateChanged.connect(self.auto_location)

        self.leditCoreLocation = QLineEdit('')
        self.leditCoreLocation.setEnabled(False)

        self.btnCoreLocation = QPushButton('...')
        self.btnCoreLocation.setEnabled(False)
        self.btnCoreLocation.clicked.connect(self.choose_location)

        self.teditLog = QTextEdit()
        self.teditLog.setReadOnly(True)
        
        self.chkboxKeepDownload = QCheckBox('Keep Downloaded Cores')
        self.chkboxKeepDownload.setChecked(False)


        self.btnGrabCores = QPushButton('Grab Cores')
        self.btnGrabCores.clicked.connect(self.grab_cores)

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.chkboxPlatformDetect)
        layout.addWidget(self.cmbboxPlatform)
        layout.addWidget(self.chkboxLocationDetect)
        layout.addWidget(self.leditCoreLocation)
        layout.addWidget(self.btnCoreLocation)
        layout.addWidget(self.teditLog)
        layout.addWidget(self.chkboxKeepDownload)
        layout.addWidget(self.btnGrabCores)

        # Set dialog layout
        self.setLayout(layout)

    def auto_platform(self):
        if self.chkboxPlatformDetect.isChecked():
            self.cmbboxPlatform.setEnabled(False)
        else:
            self.cmbboxPlatform.setEnabled(True)

    def auto_location(self):
        if self.chkboxLocationDetect.isChecked():
            self.leditCoreLocation.setEnabled(False)
            self.btnCoreLocation.setEnabled(False)
        else:
            self.leditCoreLocation.setEnabled(True)
            self.btnCoreLocation.setEnabled(True)

    def choose_location(self):
        directory = QFileDialog.getExistingDirectory(self, 'Choose Target Location', '/home')

        self.leditCoreLocation.insert(directory)

    def grab_cores(self):
        self.teditLog.insertPlainText('Starting UFO Grabber')
        """ Where the magic happens """

        # If a platform and/or architecture is not supplied it is grabbed automatically
        platform = self.get_platform()  # TODO: rename this var to prevent conflict
        architecture = self.get_architecture()
        location = CORE_LOCATION[platform]

        self.download_cores(platform, architecture)
        self.extract_cores(location)

        if not args.keep:
            self.clean_up()

    def get_platform(self):
        """ Gets the Platform and Architecture if not supplied """

        if platform.system() == 'Linux':
            return 'linux'

        elif platform.system() == 'Windows' or 'MSYS_NT' in platform.system():  # Checks for MSYS environment as well
            return 'windows'
        else:
            print('ERROR: Platform not found or supported')
            sys.exit(0)

    def get_architecture(self):
        """ Gets the Platform and Architecture if not supplied """

        if '64' in platform.architecture()[0]:
            return 'x86_64'

        elif '32' in platform.architecture()[0]:
            return 'x86'
        else:
            print('ERROR: Architecture not found or supported')
            sys.exit(0)

    def download_cores(self, _platform, _architecture):
        """ Downloads every core to the working directory """

        cores = []

        # Makes core directory to store archives if needed
        if not os.path.isdir('cores'):
            os.makedirs("cores")

        # Downloads a list of all the cores available
        urlretrieve('{}/{}/{}/latest/.index-extended'.format(URL, _platform, _architecture),
                    'cores/index')
        self.teditLog.insertPlainText('Obtained core index!')

        # Adds all the core's file names to a list
        core_index = open('cores/index')

        for line in core_index:
            file_name = line.split(' ', 2)[2:]
            cores.append(file_name[0].rstrip())
        core_index.close()
        cores.sort()

        # Downloads each core from the list
        for core in cores:
            urlretrieve('{}/{}/{}/latest/{}'.format(URL, _platform, _architecture, core),
                        'cores/{}'.format(core))
            print('Downloaded {} ...'.format(core))

        # Removes index file for easier extraction
        os.remove('cores/index')

    def extract_cores(self, _location):
        """ Extracts each downloaded core to the RA core directory """
        print('Extracting all cores to: {}'.format(_location))

        for file in os.listdir('cores'):
            archive = zipfile.ZipFile('cores/{}'.format(file))
            archive.extractall(_location)
            print('Extracted {} ...'.format(file))

    def clean_up(self):
        """ Removes all the downloaded files """
        if os.listdir('cores'):
            rmtree('cores/')


if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()
    # Run the main Qt loop
    sys.exit(app.exec_())