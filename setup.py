import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "backslash", "__version__.py")) as version_file:
    exec(version_file.read()) # pylint: disable=W0122

_INSTALL_REQUIRES = [
    "GitPython",
    "Logbook",
    "munch",
    "requests",
    "sentinels",
    "URLObject",
]

setup(name="backslash",
      classifiers = [
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: 3.4",
          "Programming Language :: Python :: 3.5",
          ],
      description="Client library for the Backslash test reporting service",
      license="BSD3",
      author="Rotem Yaari",
      author_email="vmalloc@gmail.com",
      version=__version__, # pylint: disable=E0602
      packages=find_packages(exclude=["tests"]),

      url="https://github.com/vmalloc/backslash-python",

      install_requires=_INSTALL_REQUIRES,
      scripts=[],
      namespace_packages=[]
      )
