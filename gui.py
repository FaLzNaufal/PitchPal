import sounddevice as sd
import numpy as np
import tkinter as tk
import soundfile as sf
import pitch_detection as pd
from tkinter import *
from tkinter import font
from threading import Thread, Event

# variables
target_notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
current_target_note = 0

class StreamThread(Thread):
    def __init__(self):
        super().__init__()
        self.input_device_index = 0
        self.output_device_index = 4
        self.BLOCK_SHIFT = 12000
        self.SAMPLING_RATE = 48000
        self.BLOCK_LEN = 512
        self.SOUND_DEVICE_LATENCY = 0.2

    def run(self):
        self.event = Event()
        with sd.Stream(device=(self.input_device_index, self.output_device_index),
                   samplerate=self.SAMPLING_RATE, blocksize=self.BLOCK_SHIFT,
                   dtype=np.float32,
                   channels=1, callback=lambda indata, outdata, frames, time, status, detection_callback=self.detection_callback: pd.callback(indata, outdata, frames, time, status, detection_callback)) as self.stream:
            self.event.wait()

    def terminate(self):
        self.stream.abort() # abort the stream processing
        self.event.set() # break self.event.wait()

    def detection_callback(self, closest_note):
        global app
        global current_target_note
        global target_notes

        if closest_note==None:
            app.input_note.config(fg="white")
            app.input_note.config(text="...")
            return
        
        if app.input_note.cget("text") == closest_note:
            return
        
        app.input_note.config(text=closest_note)
        if app.input_note.cget("text") == app.target_note.cget("text"):
            app.input_note.config(fg="green")
            current_target_note = (current_target_note + 1) % len(target_notes)
            app.previous_target_note.config(text=target_notes[current_target_note - 1])
            app.target_note.config(text=target_notes[current_target_note])
            app.next_target_note.config(text=target_notes[(current_target_note + 1) % len(target_notes)])
        else:
            app.input_note.config(fg="red")

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # setup
        self.title("HPS Music Trainer")
        self.geometry("400x400")
        self.minsize(400, 400)

        # fonts
        default_font = font.nametofont("TkDefaultFont")

        self.notes_font = default_font.copy()
        self.notes_font.configure(size=36)

        self.preview_notes_font = default_font.copy()
        self.preview_notes_font.configure(size=24)


        # container
        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # frames
        self.frames = {}
        for F in (HomePage, PracticePage):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            frame.configure(bg="#252526")

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()


class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # container
        self.container = Frame(self)
        self.container.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.container.configure(bg="#252526")

        # title
        title = Label(self.container, text="HPS Music Trainer", font=controller.preview_notes_font, bg="#252526", fg="white")
        title.grid(row=0, column=0, sticky=NSEW, columnspan=3, pady=(0, 50))

        # buttons
        start_button = Button(self.container, width=15,
                            command=lambda: controller.show_frame("PracticePage"),
                            text="Start Practice", bg="#2d2d30", fg="white")
        start_button.grid(row=1, column=0, sticky=NSEW, columnspan=3)

        settings_button = Button(self.container, width=15,
                            command=lambda: print("Settings"),
                            text="Settings", bg="#2d2d30", fg="white")
        settings_button.grid(row=2, column=0, sticky=NSEW, columnspan=3, pady=(10, 0))

        about_button = Button(self.container, width=15,
                            command=lambda: print("About"),
                            text="About", bg="#2d2d30", fg="white")
        about_button.grid(row=3, column=0, sticky=NSEW, columnspan=3, pady=(10, 0))
        

class PracticePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # container
        self.container = Frame(self)
        self.container.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.container.configure(bg="#252526")

        # notes
        target_note_label = Label(self.container, text="Target Note: ", bg="#252526", fg="white")
        target_note_label.grid(row=0, column=0, sticky=NSEW, columnspan=3)

        controller.previous_target_note = Label(self.container, text=target_notes[current_target_note - 1], font=controller.preview_notes_font, bg="#252526", fg="grey")
        controller.previous_target_note.grid(row=1, column=0, sticky=NSEW)

        controller.target_note = Label(self.container, text=target_notes[current_target_note], font=controller.notes_font, bg="#252526", fg="white")
        controller.target_note.grid(row=1, column=1, sticky=NSEW, padx=30)

        controller.next_target_note = Label(self.container, text=target_notes[(current_target_note + 1) % len(target_notes)], font=controller.preview_notes_font, bg="#252526", fg="grey")
        controller.next_target_note.grid(row=1, column=2, sticky=NSEW)

        input_note_label = Label(self.container, text="Input Note: ", bg="#252526", fg="white")
        input_note_label.grid(row=2, column=0, sticky=NSEW, columnspan=3, pady=(50, 0))

        controller.input_note = Label(self.container, text="...", font=controller.notes_font, bg="#252526", fg="white")
        controller.input_note.grid(row=3, column=0, sticky=NSEW, columnspan=3)

        # buttons
        start_button = Button(self.container, width=15,
                         command=start_button_clicked,
                         text="Start", bg="#2d2d30", fg="white")
        start_button.grid(row=7, column=0, sticky=NSEW, columnspan=3, pady=(50, 0))

        stop_button = Button(self.container, width=15,
                         command=stop_button_clicked,
                         text="Stop", bg="#2d2d30", fg="white")
        stop_button.grid(row=8, column=0, sticky=NSEW, columnspan=3, pady=(10, 0))

# functions
def start_button_clicked():
    stream_thread.start()

def stop_button_clicked():
    if stream_thread.is_alive():
        stream_thread.terminate()
        stream_thread.join()

if __name__ == "__main__":
    stream_thread = StreamThread()
    stream_thread.daemon = True  # set Daemon thread

    app = App()
    app.mainloop()