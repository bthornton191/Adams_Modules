pip uninstall -y adamspy
cd rst
sphinx-apidoc -f -o source ..\adamspy
call make html
cd ..
robocopy rst\build\html docs /e /mir
TIMEOUT  20
pip install adamspy