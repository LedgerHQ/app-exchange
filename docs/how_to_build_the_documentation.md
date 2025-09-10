How to build the documentation portal on local

#### Install python dependencies

```sh
pip install -Ur requirements.txt
```

#### Clone dependencies repositories

```sh
python clone_dependencies.py
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
