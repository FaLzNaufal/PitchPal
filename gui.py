import sounddevice as sd
import numpy as np
import tkinter as tk
import soundfile as sf
import pitch_detection as pd
from tkinter import *
from tkinter import font
from threading import Thread, Event
import json
import os
import sys

# variables
target_notes = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
current_target_note = 0

class StreamThread(Thread):
    def __init__(self):
        super().__init__()
        self.input_device_index = 0
        self.output_device_index = 4

    def run(self):
        user_settings = json.load(open("user_settings.json", "r"))
        sample_freq = user_settings["sample_freq"]
        window_step = user_settings["window_step"]
        self.event = Event()
        with sd.Stream(device=(self.input_device_index, self.output_device_index),
                        samplerate=sample_freq, blocksize=window_step, 
                        dtype=np.float32, channels=1,
                        callback=lambda indata, outdata, frames, time, status, detection_callback=self.detection_callback:
                        pd.callback(indata, outdata, frames, time, status, detection_callback)) as self.stream:
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
        self.title("PitchPal")
        self.geometry("500x500")
        self.minsize(500, 500)

        # fonts
        default_font = font.nametofont("TkDefaultFont")

        self.notes_font = default_font.copy()
        self.notes_font.configure(size=36)

        self.preview_notes_font = default_font.copy()
        self.preview_notes_font.configure(size=24)

        self.title_font = default_font.copy()
        self.title_font.configure(size=24, weight="bold")

        self.sub_title_font = default_font.copy()
        self.sub_title_font.configure(size=18)


        # container
        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # frames
        self.frames = {}
        for F in (HomePage, PracticePage, SettingsPage):
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
        title = Label(self.container, text="PitchPal", font=controller.title_font, bg="#252526", fg="white")
        title.grid(row=0, column=0, sticky=NSEW, pady=(0, 10))

        # sub-title
        sub_title = Label(self.container, text="Your Musical Instrument Trainer", font=controller.sub_title_font, bg="#252526", fg="#adadad")
        sub_title.grid(row=1, column=0, sticky=NSEW, pady=(0, 50))

        # buttons
        start_button = Button(self.container, width=20,
                            command=lambda: controller.show_frame("PracticePage"),
                            text="Start Practice", bg="#2d2d30", fg="white")
        start_button.grid(row=2, column=0, sticky=NS)

        settings_button = Button(self.container, width=20,
                            command=lambda: controller.show_frame("SettingsPage"),
                            text="Settings", bg="#2d2d30", fg="white")
        settings_button.grid(row=3, column=0, sticky=NS, pady=(10, 0))

        about_button = Button(self.container, width=20,
                            command=lambda: print("About"),
                            text="About", bg="#2d2d30", fg="white")
        about_button.grid(row=4, column=0, sticky=NS, pady=(10, 0))

class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # container
        self.container = Frame(self)
        self.container.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.container.configure(bg="#252526")

        # menu-title
        menu_title = Label(self.container, text="Settings", font=controller.sub_title_font, bg="#252526", fg="white")
        menu_title.grid(row=1, column=0, sticky=NSEW, pady=(0, 50), columnspan=2)

        # settings
        settings = json.load(open("user_settings.json", "r"))
        
        sample_freq_label = Label(self.container, text="Sample Frequency: ", bg="#252526", fg="white")
        sample_freq_label.grid(row=2, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        sample_freq_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        sample_freq_entry.insert(0, settings["sample_freq"])
        sample_freq_entry.grid(row=2, column=1, sticky=NE, pady=(0, 10))

        window_size_label = Label(self.container, text="Window Size: ", bg="#252526", fg="white")
        window_size_label.grid(row=3, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        window_size_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        window_size_entry.insert(0, settings["window_size"])
        window_size_entry.grid(row=3, column=1, sticky=NE, pady=(0, 10))

        window_step_label = Label(self.container, text="Window Step: ", bg="#252526", fg="white")
        window_step_label.grid(row=4, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        window_step_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        window_step_entry.insert(0, settings["window_step"])
        window_step_entry.grid(row=4, column=1, sticky=NE, pady=(0, 10))

        num_hps_label = Label(self.container, text="Number of Harmonic Product Spectrum: ", bg="#252526", fg="white")
        num_hps_label.grid(row=5, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        num_hps_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        num_hps_entry.insert(0, settings["num_hps"])
        num_hps_entry.grid(row=5, column=1, sticky=NE, pady=(0, 10))

        power_thresh_label = Label(self.container, text="Power Threshold: ", bg="#252526", fg="white")
        power_thresh_label.grid(row=6, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        power_thresh_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        power_thresh_entry.insert(0, settings["power_thresh"])
        power_thresh_entry.grid(row=6, column=1, sticky=NE, pady=(0, 10))

        concert_pitch_label = Label(self.container, text="Concert Pitch: ", bg="#252526", fg="white")
        concert_pitch_label.grid(row=7, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        concert_pitch_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        concert_pitch_entry.insert(0, settings["concert_pitch"])
        concert_pitch_entry.grid(row=7, column=1, sticky=NE, pady=(0, 10))

        white_noise_thresh_label = Label(self.container, text="White Noise Threshold: ", bg="#252526", fg="white")
        white_noise_thresh_label.grid(row=8, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        white_noise_thresh_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        white_noise_thresh_entry.insert(0, settings["white_noise_thresh"])
        white_noise_thresh_entry.grid(row=8, column=1, sticky=NE, pady=(0, 10))

        # buttons
        save_button = Button(self.container, width=20,
                            command=lambda: self.save_settings(sample_freq_entry, window_size_entry, window_step_entry, num_hps_entry, power_thresh_entry, concert_pitch_entry, white_noise_thresh_entry),
                            text="Save & Restart", bg="#2d2d30", fg="white")
        save_button.grid(row=9, column=0, sticky=SW, pady=(50, 0))

        back_button = Button(self.container, width=20,
                            command=lambda: controller.show_frame("HomePage"),
                            text="Back", bg="#2d2d30", fg="white")
        back_button.grid(row=9, column=1, sticky=SE, pady=(50, 0))

        # footer
        info_label = Label(self.container, text="Application must be restarted for changes to take effect", bg="#252526", fg="#adadad")
        info_label.grid(row=10, column=0, sticky=NSEW, columnspan=2, pady=(50, 0))



    def save_settings(self, sample_freq_entry, window_size_entry, window_step_entry, num_hps_entry, power_thresh_entry, concert_pitch_entry, white_noise_thresh_entry):
        user_settings = {
            "sample_freq": int(sample_freq_entry.get()),
            "window_size": int(window_size_entry.get()),
            "window_step": int(window_step_entry.get()),
            "num_hps": int(num_hps_entry.get()),
            "power_thresh": float(power_thresh_entry.get()),
            "concert_pitch": int(concert_pitch_entry.get()),
            "white_noise_thresh": float(white_noise_thresh_entry.get())
        }

        with open("user_settings.json", "w") as f:
            json.dump(user_settings, f, indent=2)

        print("Settings saved")

        # restart the application
        restart_program()


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
        start_button = Button(self.container, width=20,
                         command=start_button_clicked,
                         text="Start", bg="#2d2d30", fg="white")
        start_button.grid(row=7, column=0, sticky=NS, columnspan=3, pady=(50, 0))

        stop_button = Button(self.container, width=20,
                         command=stop_button_clicked,
                         text="Stop", bg="#2d2d30", fg="white")
        stop_button.grid(row=8, column=0, sticky=NS, columnspan=3, pady=(10, 0))

# functions
def start_button_clicked():
    stream_thread.start()

def stop_button_clicked():
    if stream_thread.is_alive():
        stream_thread.terminate()
        stream_thread.join()

def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)

if __name__ == "__main__":
    stream_thread = StreamThread()
    stream_thread.daemon = True  # set Daemon thread

    app = App()
    app.mainloop()