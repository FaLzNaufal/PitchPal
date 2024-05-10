# PitchPal

PitchPal is a desktop application that trains musical instrument skills by utilizing pitch detection algorithm. The application is built entirely in Python and uses tkinter for the GUI.

## Features

- Customizable practice sessions
- Real-time pitch detection
- Adjustable pitch detection parameters
- Visual feedback on note accuracy

## Installation

1. Clone the repository
2. Install the required packages

```bash
pip install -r requirements.txt
```

3. Run the gui

```bash
python gui.py
```

alternatively, you can run the executable file

## Usage

1. Pick up your instrument of choice (guitar or piano recommended)
2. Adjust the settings to your liking
3. Modify, Create, or Delete practice sessions as needed
4. Start a practice session and play the notes displayed on the screen
5. Get feedback on your note accuracy and improve your skills!

## Musical Notes

The notes used in the practice sessions are based on the 12-tone equal temperament tuning system. These are the notes that can be played in the practice sessions:

```
C, C#, D, D#, E, F, F#, G, G#, A, A#, B
```

The program reads notes in the format of `note-octave`, for example `C4` is middle C.
