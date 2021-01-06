# TopoLoco

A Game to learn Topography

**Search** the asked location on a map or **type** the name of the asked location!

Ever extending **online library** of levels created by you or myself

Here, get a glimpse of how it looks: [video](https://user-images.githubusercontent.com/66920279/103822251-07a8e300-5070-11eb-9255-3a7a21a04331.mp4)



For now: only **German** is available



___





### Installation

#### Windows

Just run the provided installer executable. 

You can follow the manual installation as well.



#### Other Operating Systems

Untested!!! Built-in Levels should work but nothing is guaranteed. (See Currently Known Limitations)

Look **Manual Installation**



#### Manual Installation

1. Install **Python 3.9** (min. 3.8) from [**here**](https://www.python.org/downloads/)

2. Download **source code** and unzip it to a new folder.

3. Create a **virtual environment** if you don't want to clutter your Python installation.
   (Skip if you don't care [if you don't use Python regularly, you probably don't ])

   1. Open Terminal and navigate to your previously created folder (probably using `cd` command)

   2. Execute `python -m venv venv`, install `python-venv` if necessary

   3. **Activate** virtual environment: 

      - Linux & Mac: `source ./venv/bin/activate`

      - Windows: `./venv/Scripts/activate`

4. Install **dependencies**:

   - Execute `pip install pygame==2.0.1 requests==2.25.1 packaging==20.8 easing-functions==1.0.3`
     (if you didn't use a virtual environment use `python -m pip install ...`)

5. Pretty much done:

   - To run TopoLoco activate 

6. Create a **shortcut** for convenience:

   - **Windows**:

     1. Create a `.bat` file to launch `topoloco.py` :

           If you are using a **virtual environment**:

           1. Locate `topoloco.py` in downloaded source folder and copy its path (something like `C:\<User>\Documents\topoloco\topoloco.py`)

             2. Locate `pythonw.exe` inside `venv/Scripts/` and copy its path (something like `C:\<User>\Documents\topoloco\venv\Scripts\pythonw.exe`)

             3. Open a text editor (like notepad / editor / notepad ++) and type:

                    ```bat
                  @echo off
                  start "topoloco" /D <path-to-sourcefolder-root> <path-to-pythonw.exe> topoloco.py
                    ```

                    Example `run.bat`:      

                    ```bat
                  @echo off
                  start "topoloco" /D D:\<user>\topoloco\py_topoloco D:\<user>\topoloco\py_topoloco\venv\Scripts\pythonw.exe topoloco.py
                    ```

                  4. Save file as `run.bat` be sure that the file ends with`.bat`!

           If **not**:

           1. Locate source folder and copy its path (something like `C:\<User>\Documents\topoloco\`, it contains `topoloco.py` )
           2. Open a text editor (like notepad / editor / notepad ++) and type:

           ```bat
           @echo off
           start "topoloco" /D <path-to-sourcefolder-root> pythonw topoloco.py
           ```

            Example `run.bat`:  
           ```bat
           @echo off
           start "topoloco" /D C:\<User>\Documents\topoloco\  pythonw topoloco.py
           ```

           ​	3. Save file as `run.bat` be sure that the file ends with`.bat`!

       2. Right-click on your `run.bat` file and select `Send-To/Desktop`. There you have your shortcut!

   - **Linux**:

     - If you have a solution, let me know

   - **Mac**:

     - Here too, let me know if you know a solution



### Currently Known Limitations

- Update mechanism works only on Windows

- Online Library only on Windows working (probably, idk because I haven't tested it)

  

### Custom Levels

If you've created a level, feel free to create an issue or contact me, so I can include it into the Online Library

#### How to create one

A level contains of a `json` file and a `png` or other image format file.

The `json` file is pretty straightforward, just look into existing levels.

A hint though:

- The coordinates are relative to the image



### Todo

- [ ] Localization
- [ ] Platform independency
- [ ] Code clean up (like Dependency injection)
- [ ] Level creator/editor
- [ ] More levels
- [ ] smarter marker choosing algorithm than just random
- [ ] category selector
- [ ] different colored marker
- [ ] better animated UI, improve overall UX
- [ ] idk, whatever bug appears or feature suggestions





---



Now, the more technical things



### Installer

The installer is built using `pynsist`.

`pynsist installer.cfg`



### Contributions

Feel free to create PRs and or contact me directly if anything bothers you. 

#### Bugs/Issues/Suggestion/Feature requests etc.

Create an issue or if don't know how this works (like me) contact me directly 

#### Other Platforms

You are welcome to contribute your improvements on platform compatibility. Like fiddling around with `pyinstaller` to create executables that work :)



### Dependencies

On Python **3.9.1** developed and tested (Windows only for now)

##### Pip packages:

- `pygame==2.0.1`
- `easing-functions==1.0.3`
- `packaging==20.8`
- `requests==2.25.1`



### Helpful Links

- Structure of game using scenes in PyGame (I forgot where it was :( )
- uuhm, if I remember them again, I will update 



Now again: drop in every single comment, feedback and contribution somewhere on GitHub or into my mail-inbox,

I'd really appreciate that! :)



You find contact information on the about page inside TopoLoco and here somewhere.



