Basic chess in pygame

## Requirements
Python3.6 must be installed and used due to pygame 1.9.6 dependency on it

## Install
```
git clone git@github.com:cknolla/pygame-chess.git
cd pygame-chess
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Controls
Key | Command
--- | ---
Q or ESC | Quit
R | Reset
Left Click | Select piece / move
Right Click | Cancel piece selection

## Notes
- Log of actions will appear in console, and if a move is not allowed, it will be explained there
