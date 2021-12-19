# testGUI
##### (VersaMe, Inc)
- - -

### Overview

`testGUI` is the PyQt GUI application that tests VersaMe's Starling hardware. It is intended to run in tester firmware.

### What is this repository for? ###

* GUI for test firmware.
* 0.3.


### How do I get set up? ###

* testgui.py is the source file. It's built by PyQt. testgui_app is the source file for execution app. dist/ folder contains exe file. build folder contains library.
* Run testgui_app in dist/ folder, it will open a gui.
* First Download the latest test firmware from master. Download testGUI repository in /home/code/ folder. Open the Gui from testgui_app file in dist folder.

### Prerequisites

+ SEGGER [JLink software](http://www.segger.com/jlink-software.html)
+ minicom
```

brew install minicom

```

### Local Dependencies

The dist/ and build/ folders are created by pyinstaller. you can execute the GUI program by simply open the testgui_app file in dist/ folder without installing Library.

### Building Prerequisites

+ Adafruit_Python_BlueFruitLE Library
+ pyserial-2.7
+ SIP
+ PyQt
+ pyobjc-3.0.4
+ PyInstaller-3.1.1
+ zebra-0.0.5

### Library Configuration

Install pyserial-2.7, pyobjc-3.04, PyInstaller-3.1.1, and zebra-0.0.5 through pip:

```

pip install -r requirements.txt

```

go to lib/Adafruit_Python_BluefruitLE-master:

```

python setup.py install

```

Install sip through brew

```

brew install sip

```

Install pyqt through brew

```

brew install pyqt

```

Add one line to ~/.bash_profile

```

export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python2.7/site-packages¬

```

### Building Executable file
In src/ folder

```

rm -rf ../build ../dist
pyinstaller testgui_app.py --onefile --windowed --distpath ../dist --workpath ../build

```

### Building Virtual Environment

```
rm -rf env/
virtualenv --no-site-packages env
cd env
source bin/activate
deactivate

```