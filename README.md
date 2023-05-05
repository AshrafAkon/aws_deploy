### Cli written in Python to make Deployment easier

In order to use this. You need the latest version of python installed.
After that follow the steps below.

1. move to the `cli` directory (the parent directory of this file)
2. Create python virtual environment with `python3 -m venv env`
3. Active virtual env with `source env/bin/activate`
4. Install python dependencies with `python3 -m pip install -r requirements.txt`
5. Install the cli in virtual environment with `pip install -e .`

### Basics

1. View available commands with `deploy --help`
2. View options of individual command with `deploy COMMAND --help`

#### Creating Stack

1. `deploy create-stack -n STACK_NAME` Ex: `deploy create-stack -n resources`

#### Creating multiple stack at once

1. Deploy core with `deploy create-stacks -c`
2. Deploy all services according to config yml files
   with `deploy create-stack -s`

