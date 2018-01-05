# Quickstart for Python Google App Engine

## Setup

### Ensure Python 2.7 is on your path:
```
python --version
```
If missing or wrong version, install from [https://www.python.org/downloads/](https://www.python.org/downloads/) and add to your path.

### Create a virtual environment
- Verify that `virtualenv` is installed:
```
virtualenv --help
```

- If it is not installed, installed it with `pip`:
```
pip install virtualenv
```

- Create the virtual environment `venv`
```
virtualenv venv
```

- Activate the virtual environment
    - Windows DOS command: `venv\scripts\activate.bat`
    - Windows Powershell: `venv\scripts\activate.ps1`
    - Bash: `source venv/bin/activate`

### Install requirements
```
pip install -r requirements.txt
```

## Run locally

From command line (DOS, Powershell, bash):
```
python main.py
```

## Using Visual Studio Code

### Setup
- Install [Python extension](https://marketplace.visualstudio.com/items?itemName=donjayamanne.python):
    Launch VS Code Quick Open (Ctrl+P), paste the following command, and press enter
    ```ext install python```
- Read extension [documentation](https://github.com/DonJayamanne/pythonVSCode/wiki) and particular, the documentation about 
[linting](https://github.com/DonJayamanne/pythonVSCode/wiki/Linting).


### Using environment
To let Visual Studio code find the correct python interpreter and libraries for debugging and intellisense.
- From the command line (with virtual environment activated): environment picked automatically
    ``` vscode . ```
- When opening Visual Studio Code from file explorer (Open with Code menu):
    Set the environment from the [command palette](https://code.visualstudio.com/docs/editor/codebasics#_command-palette): `Ctrl+Shift+P`
    ```
    python select workspace interpreter
    ```
    Choose the `python` executable under your local `venv` directory.

### Debugging
Like Visual Studio, press `F9` to set a break point, `F5` to start debugging
There are [diffent ways to debug Flask](https://github.com/DonJayamanne/pythonVSCode/wiki/Debugging:-Flask).
This example is setup for [Flask debugging solution 2](https://github.com/DonJayamanne/pythonVSCode/wiki/Debugging:-Flask#solution-2).

## Deploy

### Ensure that your Google configuration points to the correct project
```
gcloud config list
```
### Setup site packages for deployment
** Windows setup is different from Linux/Mac**
- In [appengine_config.py](./appengine_config.py)
    - Mac/Linux
    ```python
    vendor.add('venv/lib/python2.7/site-packages')
    ```
    - Windows
    ```python
    vendor.add('venv/Lib/site-packages')
    ```  
- In [app.std.yaml](./app.std.yaml)
  - Mac/Linux
  ```yaml
  skip_files:
  - (venv/lib/python2.7/site-packages/appengine_sdk.*)
  - (venv/lib/python2.7/site-packages/setuptools/.*)
  - (venv/lib/python2.7/site-packages/nose.*)
  - (venv/lib/python2.7/site-packages/pip.*)
  ```
  - Windows
  ```yaml
  skip_files:
  - (venv/Lib/site-packages/appengine_sdk.*)
  - (venv/Lib/site-packages/setuptools/.*)
  - (venv/Lib/site-packages/nose.*)
  - (venv/Lib/site-packages/pip.*)
  ```

### Deploy to Standard App Engine
```
gcloud app deploy --version=v1 app.std.yaml
```

## Browse
- Service: `https://talk-demo-dot-<projectname>.appspot.com`
    - You can also use `gcloud app browse -s talk-demo`
- default: `https://<projectname>.appspot.com`
    - You can also use `gcloud app browse`

## Emulators

```bash
gcloud beta emulators datastore start &
`gcloud beta emulators datastore env-init`

# emulators - start
gcloud beta emulators pubsub start &
`gcloud beta emulators pubsub env-init`

# emulators - kill
pkill -f emulators
unset PUBSUB_EMULATOR_HOST

```


