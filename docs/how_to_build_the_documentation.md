# How to build the documentation portal locally

This document is intended at developers or reviewers of the documentation, it is not included in the documentation portal itself.

#### Install python dependencies

```sh
pip install -Ur docs/requirements.txt
```

#### Clone dependencies repositories

```sh
python docs/clone_dependencies.py
```

#### Run the documentation builder server

```sh
# Run in the main exchange repository
mkdocs serve
```

#### Access the local documentation portal

```sh
firefox http://127.0.0.1:8000/ &
```
