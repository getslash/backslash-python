#! /usr/bin/python
import subprocess

if __name__ == '__main__':
    subprocess.check_call("pip install --use-mirrors -r test_requirements.txt", shell=True)
    subprocess.check_call("python setup.py develop", shell=True)
    subprocess.check_call("py.test tests", shell=True)
