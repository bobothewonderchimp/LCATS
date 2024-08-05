# LCATS Python package 'lcats'
Python implementation of LCATS, a large language model version of the 
Captain's Advisory Tool System. This includes tools for extracting data
from various sources into local corpora, and will later contain more
sophisticated tools built on top of these corpora.

## Requirements
Right now, some requirements are via pip and others via conda. :-/
- Python > 3.6(ish)
- pip install build  # can be conda installed: conda install conda-forge::python-build
- pip install twine  # can be conda installed: conda install conda-forge::twine
- pip install beautifulsoup4
- pip install lxml
- conda install -c anaconda pytest
- conda install conda-forge::parameterized


## Building
```
# Get the repository
gh repo clone xenotaur/LCATS

# Change to the Python pacakge directory.
cd LCATS/lcats

# Tests using the unittest package
scripts/test

# Local development using an editable local pip installation.
scripts/clean && scripts/build && scripts/develop
lcats info
lcats gather
```
Publishing this package to PyPI is not yet supported because we don't yet have extensive enough tests.