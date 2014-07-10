#For Users#

##Running the Application##

1. Download the Flipbook package for your Operating System
2. On Windows:
	- Launche the installer, it will install the software and create shortcuts in the Start Menu.
	- Run the application using the shortcut **Flipbook**
	- On Windows 8, one might have to disable installation of 
3. On Mac:
	- Extract the application from the zip folder. Optionally, drag the green application icon to the Application Folder.
	- Run the application by clicking on the **Flipbook** application icon.


###System Requirement###
* Windows Vista, 7, or 8 (64bit)
* Mac OS X 10.6+ (Intel CPU)
* A relatively modern graphics card (2010 or later computer should be okay)
* Internet Connection for certain functionalities (PDB fetching, Upload)


###Basic 3D Controls###
* Right Click: Pan view
* Scroll Wheel: Zoom view
* Left Click: Orbit view

The application is designed to be used with a mouse. If you are on a laptop with trackpad, you can use Ctrl+Left Click to emulate a right click.


###File Storage###
After Flipbook has been started for the first time, it will create a folder under `~/Flipbook/` as its temporary folder. Program data, error log, data cache, and finished videos will be stored to this folder. This folder serves as a cache to speed up future access of data.

##Known Problems##

**Problematic PDBs**

Certain PDBs might not import properly or cause instabilities with the application. This is something we are constantly working on. But if a particular PDB causes problems, try the following:

1. Enable 'Large Solvent Radius' in the import dialog.
2. Disable 'use bioMT' in the import dialog.
3. Report the PDB to us and we'll try to fix it.

**File Extentions**

On Windows, The Flipbook application will also register the .flipbook file extension so that saved files can be opened with Flipbook by clicking on them.

On Mac, currently the file extension is not associated with the application. To open a session file, use the Load Scene button from within Flipbook.


**Windows 8 App Signing**

Some user reported problems with installing the application on Windows 8. Make sure you turn off any antivirus software. It might also help to run the installer as an Administrator by right clicking on the installer exe and select 'Run as Administrator'.

**Linux Version**

Due to the limited resources we have and the limtations of the third-party libraries we are using, a Linux version is currently not available. But we hope it's something that will be available in the future!



