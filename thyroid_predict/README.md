# Thyroid Predict User Interface

**About**\
\
It is a user interface to utilize the binary tyroid malignant cytology classification model. This interface is based on the <a href="https://github.com/openslide/openslide-python/tree/main/examples/deepzoom">OpenSlide Deep Zoom example project</a>, utilizing the <a href="https://flask.palletsprojects.com/en/2.0.x/">Flask framework</a> and <a href="http://openseadragon.github.io/">Open Seadragon API</a>. The OpenSlide DeepZoom example was adapted to view, extract and make inference of thyroid images. \
\
**Installation**

*Windows*

1. Download and extract zip file from <a href="#">windows distribution folder</a>
1. Download and install Microsoft Visual C++: Download <a href="https://www.microsoft.com/en-us/download/details.aspx?id=26999">Microsoft Visual C++ 2010 Service Pack 1 Redistributable Package MFC Security Update from Official Microsoft Download Center </a>
2. Click on **install.exe** file
3. Wait installation looking to black window with informations
4. Look to your Windows Workspace and find the program icon. You can delete the zip file and extracted files of Windows Downloads, if you want.

*Linux*

1. Just download the project, keep this folder and run "main.py" file. You should install the dependencies before:
    * Python 3.7 or 3.9 (recommended)
    * <a href="https://pillow.readthedocs.io/en/stable/installation.html">Pillow</a>
    * <a href="https://flask.palletsprojects.com/en/2.0.x/installation/">Flask</a>
    * <a href="https://openslide.org/download/">OpenSlide</a> on Linux Distribution Packages section