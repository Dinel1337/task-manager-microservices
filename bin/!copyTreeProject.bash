find . -type d -name "__pycache__" -exec rm -rf {} +

tree -I '.venv|.pytest_cache' --charset=ascii | tee /dev/tty | clip.exe