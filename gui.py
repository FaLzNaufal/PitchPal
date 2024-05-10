import sounddevice as sd
import numpy as np
import tkinter as tk
import pitch_detection as pd
from tkinter import *
from tkinter import font, messagebox
from threading import Thread, Event
import json
import os
import sys
import random

# variables
target_notes = []
alternate_names = []
current_target_note_idx = 0
current_practice = None
current_practice_idx = None
practice_list = []

class StreamThread(Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        user_settings = json.load(open("user_settings.json", "r"))
        sample_freq = user_settings["sample_freq"]
        window_step = user_settings["window_step"]
        self.event = Event()
        with sd.Stream(samplerate=sample_freq, blocksize=window_step, 
                        dtype=np.float32, channels=1,
                        callback=lambda indata, outdata, frames, time, status, detection_callback=self.detection_callback:
                        pd.callback(indata, outdata, frames, time, status, detection_callback)) as self.stream:
            self.event.wait()

    def terminate(self):
        self.stream.abort() # abort the stream processing
        self.event.set() # break self.event.wait()

    def detection_callback(self, closest_note):
        global app, current_target_note_idx, target_notes, alternate_names, current_practice

        has_alternate_names = current_practice.get("has_alternate_names") if current_practice else False
        is_random = current_practice.get("is_random") if current_practice else False

        if closest_note==None:
            app.input_note.config(fg="white")
            app.input_note.config(text="...")
            return
        
        if app.input_note.cget("text") == closest_note:
            return
        
        app.input_note.config(text=closest_note)
        if target_notes[current_target_note_idx] == closest_note:
            app.input_note.config(fg="green")
            if is_random:
                current_target_note_idx = get_random_list_idx(target_notes, current_target_note_idx)
            else:
                current_target_note_idx = (current_target_note_idx + 1) % len(target_notes)
            app.target_note.config(text=target_notes[current_target_note_idx] if not has_alternate_names else alternate_names[current_target_note_idx])
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
        self.default_font = font.nametofont("TkDefaultFont")

        self.notes_font = self.default_font.copy()
        self.notes_font.configure(size=36)

        self.preview_notes_font = self.default_font.copy()
        self.preview_notes_font.configure(size=24)

        self.title_font = self.default_font.copy()
        self.title_font.configure(size=24, weight="bold")

        self.sub_title_font = self.default_font.copy()
        self.sub_title_font.configure(size=18)

        # container
        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # frames
        self.frames = {}
        for F in (HomePage, PracticePage, SettingsPage, PracticeListPage, PracticeSettingsPage):
            frame = F(container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            frame.configure(bg="#252526")

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        match page_name:
            case "PracticeListPage":
                frame.refresh_listbox()
            case "PracticeSettingsPage":
                if current_practice:
                    frame.fill_form()
                else:
                    frame.clear_form()
            case "PracticePage":
                frame.init_practice()

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
                            command=lambda: controller.show_frame("PracticeListPage"),
                            text="Start Practice", bg="#2d2d30", fg="white", cursor="hand2")
        start_button.grid(row=2, column=0, sticky=NS)

        settings_button = Button(self.container, width=20,
                            command=lambda: controller.show_frame("SettingsPage"),
                            text="Settings", bg="#2d2d30", fg="white", cursor="hand2")
        settings_button.grid(row=3, column=0, sticky=NS, pady=(10, 0))

        about_button = Button(self.container, width=20,
                            command=lambda: messagebox.showinfo(
                                "About", "PitchPal is an interactive musical instrument trainer that utilizes Pitch Detection Algorithm. "\
                                "customize your own practice with your desired notes, give them alternate names, and practice the notes either "\
                                "in sequential or randomized order. Change the parameters of the Pitch Detection Algorithm (Harmonic Product "\
                                "Spectrum) to suit your likings in the settings menu. Happy practicing :)"),
                            text="About", bg="#2d2d30", fg="white", cursor="hand2")
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
        menu_title.grid(row=1, column=0, sticky=NSEW, pady=(0, 50), columnspan=3)

        # settings
        settings = json.load(open("user_settings.json", "r"))
        
        sample_freq_label = Label(self.container, text="Sample Frequency: ", bg="#252526", fg="white")
        sample_freq_label.grid(row=2, column=0, sticky=NW, pady=(0, 10), padx=(0, 20), columnspan=2)

        sample_freq_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        sample_freq_entry.insert(0, settings["sample_freq"])
        sample_freq_entry.grid(row=2, column=2, sticky=NE, pady=(0, 10))

        sample_freq_info_button = Button(self.container, text="?", bg="#252526", fg="white", width=1, height=1, command=lambda: messagebox.showinfo("Info", "The sample frequency of the input audio. Usually 44100 or 48000 Hz."), relief=FLAT, cursor="hand2", activebackground="#252526", activeforeground="white", bd=0)
        sample_freq_info_button.grid(row=2, column=3, sticky=NE, pady=(0, 10))

        window_size_label = Label(self.container, text="Window Size: ", bg="#252526", fg="white")
        window_size_label.grid(row=3, column=0, sticky=NW, pady=(0, 10), padx=(0, 20), columnspan=2)

        window_size_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        window_size_entry.insert(0, settings["window_size"])
        window_size_entry.grid(row=3, column=2, sticky=NE, pady=(0, 10))

        window_size_info_button = Button(self.container, text="?", bg="#252526", fg="white", width=1, height=1, command=lambda: messagebox.showinfo("Info", "The size of the window for the DFT in samples. Larger values means more samples to process"), relief=FLAT, cursor="hand2", activebackground="#252526", activeforeground="white", bd=0)
        window_size_info_button.grid(row=3, column=3, sticky=NE, pady=(0, 10))

        window_step_label = Label(self.container, text="Window Step: ", bg="#252526", fg="white")
        window_step_label.grid(row=4, column=0, sticky=NW, pady=(0, 10), padx=(0, 20), columnspan=2)

        window_step_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        window_step_entry.insert(0, settings["window_step"])
        window_step_entry.grid(row=4, column=2, sticky=NE, pady=(0, 10))

        window_step_info_button = Button(self.container, text="?", bg="#252526", fg="white", width=1, height=1, command=lambda: messagebox.showinfo("Info", "The step size of the window in samples. Smaller values means faster detection intervals"), relief=FLAT, cursor="hand2", activebackground="#252526", activeforeground="white", bd=0)
        window_step_info_button.grid(row=4, column=3, sticky=NE, pady=(0, 10))

        num_hps_label = Label(self.container, text="Number of Harmonic Product Spectrum: ", bg="#252526", fg="white")
        num_hps_label.grid(row=5, column=0, sticky=NW, pady=(0, 10), padx=(0, 20), columnspan=2)

        num_hps_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        num_hps_entry.insert(0, settings["num_hps"])
        num_hps_entry.grid(row=5, column=2, sticky=NE, pady=(0, 10))

        num_hps_info_button = Button(self.container, text="?", bg="#252526", fg="white", width=1, height=1, command=lambda: messagebox.showinfo("Info", "The maximum number of harmonic product spectrums. Increase this value if you have trouble detecting low notes, decrease if you have trouble detecting high notes. If you are unsure, leave it at 6."), relief=FLAT, cursor="hand2", activebackground="#252526", activeforeground="white", bd=0)
        num_hps_info_button.grid(row=5, column=3, sticky=NE, pady=(0, 10))

        power_thresh_label = Label(self.container, text="Power Threshold: ", bg="#252526", fg="white")
        power_thresh_label.grid(row=6, column=0, sticky=NW, pady=(0, 10), padx=(0, 20), columnspan=2)

        power_thresh_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        power_thresh_entry.insert(0, settings["power_thresh"])
        power_thresh_entry.grid(row=6, column=2, sticky=NE, pady=(0, 10))

        power_thresh_info_button = Button(self.container, text="?", bg="#252526", fg="white", width=1, height=1, command=lambda: messagebox.showinfo("Info", "Tuning is activated if the signal power exceeds this threshold. Increase this value if the tuner is too sensitive, decrease if it is not sensitive enough."), relief=FLAT, cursor="hand2", activebackground="#252526", activeforeground="white", bd=0)
        power_thresh_info_button.grid(row=6, column=3, sticky=NE, pady=(0, 10))

        concert_pitch_label = Label(self.container, text="Concert Pitch: ", bg="#252526", fg="white")
        concert_pitch_label.grid(row=7, column=0, sticky=NW, pady=(0, 10), padx=(0, 20), columnspan=2)

        concert_pitch_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        concert_pitch_entry.insert(0, settings["concert_pitch"])
        concert_pitch_entry.grid(row=7, column=2, sticky=NE, pady=(0, 10))

        concert_pitch_info_button = Button(self.container, text="?", bg="#252526", fg="white", width=1, height=1, command=lambda: messagebox.showinfo("Info", "The concert pitch (A4) frequency in Hz. Set this value to the frequency of A4 in Hz for your instrument."), relief=FLAT, cursor="hand2", activebackground="#252526", activeforeground="white", bd=0)
        concert_pitch_info_button.grid(row=7, column=3, sticky=NE, pady=(0, 10))

        white_noise_thresh_label = Label(self.container, text="White Noise Threshold: ", bg="#252526", fg="white")
        white_noise_thresh_label.grid(row=8, column=0, sticky=NW, pady=(0, 10), padx=(0, 20), columnspan=2)

        white_noise_thresh_entry = Entry(self.container, width=10, bg="#2d2d30", fg="white")
        white_noise_thresh_entry.insert(0, settings["white_noise_thresh"])
        white_noise_thresh_entry.grid(row=8, column=2, sticky=NE, pady=(0, 10))

        white_noise_thresh_info_button = Button(self.container, text="?", bg="#252526", fg="white", width=1, height=1, command=lambda: messagebox.showinfo("Info", "Threshold for white noise. If you are unsure, leave it at 0.2"), relief=FLAT, cursor="hand2", activebackground="#252526", activeforeground="white", bd=0)
        white_noise_thresh_info_button.grid(row=8, column=3, sticky=NE, pady=(0, 10))

        # buttons
        save_button = Button(self.container, width=15,
                            command=lambda: self.save_settings(sample_freq_entry, window_size_entry, window_step_entry, num_hps_entry, power_thresh_entry, concert_pitch_entry, white_noise_thresh_entry),
                            text="Save & Restart", bg="#2d2d30", fg="white", cursor="hand2")
        save_button.grid(row=9, column=0, sticky=SW, pady=(30, 0))

        reset_button = Button(self.container, width=15,
                            command=self.reset_settings,
                            text="Reset to Default", bg="#2d2d30", fg="white", cursor="hand2")
        reset_button.grid(row=9, column=1, sticky=SW, pady=(30, 0))

        back_button = Button(self.container, width=15,
                            command=lambda: controller.show_frame("HomePage"),
                            text="Back", bg="#2d2d30", fg="white", cursor="hand2")
        back_button.grid(row=9, column=2, sticky=SE, pady=(30, 0))

        # footer
        info_label = Label(self.container, text="Application must be restarted for changes to take effect", bg="#252526", fg="#adadad")
        info_label.grid(row=10, column=0, sticky=NSEW, columnspan=3, pady=(50, 0))



    def save_settings(self, sample_freq_entry, window_size_entry, window_step_entry, num_hps_entry, power_thresh_entry, concert_pitch_entry, white_noise_thresh_entry):
        try:
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

            messagebox.showinfo("Success", "Settings saved!")

            # restart the application
            restart_program()

        except ValueError:
            messagebox.showerror("Failed to Save", "Please enter valid values")

        except Exception as e:
            messagebox.showerror("Failed to Save", "An error occurred while saving settings")

    def reset_settings(self):
        default_settings = {
            "sample_freq": 48000,
            "window_size": 48000,
            "window_step": 3000,
            "num_hps": 6,
            "power_thresh": 1e-6,
            "concert_pitch": 440,
            "white_noise_thresh": 0.2
        }

        with open("user_settings.json", "w") as f:
            json.dump(default_settings, f, indent=2)

        messagebox.showinfo("Success", "Settings reset to default!")

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

        # title
        self.title_label = Label(self.container, text="Practice", font=controller.sub_title_font, bg="#252526", fg="white")
        self.title_label.grid(row=0, column=0, pady=(0, 10), columnspan=2, sticky=NSEW)

        # description
        self.description_label = Label(self.container, text="Practice your notes!", bg="#252526", fg="#adadad", wraplength=260, height=2, anchor=N)
        self.description_label.grid(row=1, column=0, columnspan=2, pady=(0, 30), sticky=NSEW)

        # notes
        target_note_label = Label(self.container, text="Target Note: ", bg="#252526", fg="white")
        target_note_label.grid(row=2, column=0, sticky=NSEW, columnspan=3)

        controller.target_note = Label(self.container, font=controller.notes_font, bg="#252526", fg="white")
        controller.target_note.grid(row=3, column=0, sticky=NSEW, columnspan=2)

        input_note_label = Label(self.container, text="Input Note: ", bg="#252526", fg="white")
        input_note_label.grid(row=4, column=0, sticky=NSEW, columnspan=3, pady=(30, 0))

        controller.input_note = Label(self.container, text="...", font=controller.notes_font, bg="#252526", fg="white")
        controller.input_note.grid(row=5, column=0, sticky=NSEW, columnspan=3)

        # buttons
        self.start_button = Button(self.container, width=13,
                            command=self.on_start_button_click,
                            text="Start", bg="#2d2d30", fg="white", cursor="hand2")
        self.start_button.grid(row=6, column=0, sticky=NSEW, pady=(30, 0), padx=(0, 10))

        self.stop_button = Button(self.container, width=13,
                            command=self.on_stop_button_click,
                            text="Stop", bg="#2d2d30", fg="white", state=DISABLED)
        self.stop_button.grid(row=6, column=1, sticky=NSEW, pady=(30, 0))

        self.back_button = Button(self.container, width=13,
                            command=lambda: controller.show_frame("PracticeListPage"),
                            text="Back", bg="#2d2d30", fg="white", cursor="hand2")
        self.back_button.grid(row=7, column=0, sticky=NSEW, pady=(10, 0), columnspan=2)
    
    def on_start_button_click(self):
        start_stream_thread()
        self.start_button.config(state=DISABLED, cursor="arrow")
        self.stop_button.config(state=NORMAL, cursor="hand2")

    def on_stop_button_click(self):
        stop_stream_thread()
        restart_program()

    def init_practice(self):
        global current_target_note_idx, target_notes, current_practice, alternate_names
        has_alternate_names = current_practice.get("has_alternate_names") if current_practice else False
        if current_practice and current_practice.get("is_random"): # random practice
            current_target_note_idx = get_random_list_idx(target_notes)
            self.controller.target_note.config(text=target_notes[current_target_note_idx] if not has_alternate_names else alternate_names[current_target_note_idx])
        else:
            current_target_note_idx = 0
            self.controller.target_note.config(text=target_notes[current_target_note_idx] if not has_alternate_names else alternate_names[current_target_note_idx])
        self.title_label.config(text=current_practice.get("name"))
        self.description_label.config(text=current_practice.get("description"))


class PracticeListPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # load practice_list
        practice_list = json.load(open("practice_list.json", "r"))

        # container
        self.container = Frame(self)
        self.container.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.container.configure(bg="#252526")

        # menu-title
        menu_title = Label(self.container, text="Practice List", font=controller.sub_title_font, bg="#252526", fg="white")
        menu_title.grid(row=1, column=0, sticky=NSEW, pady=(0, 30), columnspan=3)

        # listbox
        self.listbox = Listbox(self.container, bg="#2d2d30", fg="white", selectbackground="#3d3d3d", borderwidth=0, highlightthickness=0, activestyle="none", font=controller.default_font)
        for item in practice_list:
            self.listbox.insert(END, item.get("name"))
        self.listbox.grid(row=3, column=0, sticky=NSEW, columnspan=3)


        # scrollbar
        scrollbar = Scrollbar(self.container, orient="vertical", command=self.listbox.yview)
        scrollbar.grid(row=3, column=2, sticky="nse")
        self.listbox.config(yscrollcommand=scrollbar.set)


        # buttons
        self.start_button = Button(self.container, width=12,
                            command=self.on_start_button_click,
                            text="Start", bg="#2d2d30", fg="white", state=DISABLED)
        self.start_button.grid(row=4, column=0, sticky=NSEW, pady=(30, 0))


        self.modify_button = Button(self.container, width=12,
                            command=self.on_modify_button_click,
                            text="Modify", bg="#2d2d30", fg="white", state=DISABLED)
        self.modify_button.grid(row=4, column=1, sticky=NSEW, pady=(30, 0), padx=(10, 0))

        self.delete_button = Button(self.container, width=12,
                                command=self.on_delete_button_click,
                                text="Delete", bg="#2d2d30", fg="white", state=DISABLED)
        self.delete_button.grid(row=4, column=2, sticky=NSEW, pady=(30, 0), padx=(10, 0))

        new_practice_button = Button(self.container,
                            command=self.on_new_practice_button_click,
                            text="+ New Practice", bg="#2d2d30", fg="white", width=12, cursor="hand2")
        new_practice_button.grid(row=2, column=2, sticky=NE, pady=(0, 10))

        back_button = Button(self.container, width=20,
                            command=lambda: controller.show_frame("HomePage"),
                            text="Back", bg="#2d2d30", fg="white", cursor="hand2")
        back_button.grid(row=5, column=0, sticky=NSEW, pady=(10, 0), columnspan=3)

        self.listbox.bind('<<ListboxSelect>>', self.enable_buttons)

    def on_start_button_click(self):
        global current_practice, target_notes, alternate_names
        current_practice = practice_list[self.listbox.curselection()[0]]
        target_notes = [note.get("note") for note in current_practice.get("note_list")]
        alternate_names = [note.get("alternate_name") for note in current_practice.get("note_list")]
        self.controller.show_frame("PracticePage")

    def on_modify_button_click(self):
        global current_practice, current_practice_idx
        current_practice_idx = self.listbox.curselection()[0]
        current_practice = practice_list[current_practice_idx]
        self.controller.show_frame("PracticeSettingsPage")

    def on_delete_button_click(self):
        global current_practice, current_practice_idx, practice_list
        if not messagebox.askyesno("Confirmation", "Are you sure you want to delete \"" + practice_list[self.listbox.curselection()[0]].get("name") + "\"?"):
            return
        practice_list.pop(self.listbox.curselection()[0])
        with open("practice_list.json", "w") as f:
            json.dump(practice_list, f, indent=2)
        self.refresh_listbox()
        messagebox.showinfo("Success", "Practice deleted!")

    
    def on_new_practice_button_click(self):
        global current_practice, current_practice_idx, practice_list
        current_practice = None
        current_practice_idx = len(practice_list)
        self.controller.show_frame("PracticeSettingsPage")

    def enable_buttons(self, event):
        self.start_button.config(state=NORMAL, cursor="hand2")
        self.modify_button.config(state=NORMAL, cursor="hand2")
        self.delete_button.config(state=NORMAL, cursor="hand2")
    
    def refresh_listbox(self):
        global practice_list
        practice_list = json.load(open("practice_list.json", "r"))
        self.listbox.delete(0, END)
        for item in practice_list:
            self.listbox.insert(END, item.get("name"))
        self.start_button.config(state=DISABLED, cursor="arrow")
        self.modify_button.config(state=DISABLED, cursor="arrow")
        self.delete_button.config(state=DISABLED, cursor="arrow")

class PracticeSettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # container
        self.container = Frame(self)
        self.container.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.container.configure(bg="#252526")

        # menu-title
        menu_title = Label(self.container, text="Practice Settings", font=controller.sub_title_font, bg="#252526", fg="white")
        menu_title.grid(row=1, column=0, sticky=NSEW, pady=(0, 50), columnspan=2)

        # name
        name_label = Label(self.container, text="Name: ", bg="#252526", fg="white")
        name_label.grid(row=2, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        self.name_entry = Entry(self.container, width=20, bg="#2d2d30", fg="white")
        self.name_entry.grid(row=2, column=1, sticky=NE, pady=(0, 10))

        # description
        description_label = Label(self.container, text="Description: ", bg="#252526", fg="white")
        description_label.grid(row=3, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        self.description_entry = Entry(self.container, width=20, bg="#2d2d30", fg="white")
        self.description_entry.grid(row=3, column=1, sticky=NE, pady=(0, 10))

        # target notes
        target_notes_label = Label(self.container, text="Target Notes: ", bg="#252526", fg="white")
        target_notes_label.grid(row=4, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        target_notes_info_button = Button(self.container, text="?", bg="#252526", fg="white", width=1, height=1, command=lambda: messagebox.showinfo("Info", "Enter the target notes in capital letter separated by commas (e.g. A4, G#3, ..)"), relief=FLAT, cursor="hand2", activebackground="#252526", activeforeground="white", bd=0)
        target_notes_info_button.grid(row=4, column=1, sticky=NE, pady=(0, 10))

        self.target_notes_entry = Text(self.container, bg="#2d2d30", fg="white", height=2, width=20, font=controller.default_font)
        self.target_notes_entry.grid(row=5, column=0, pady=(0, 10), columnspan=2, sticky=NSEW)


        # alternate names
        self.has_alternate_names = IntVar()
        self.alternate_names_checkbox = Checkbutton(self.container, text="Has Alternate Names", variable=self.has_alternate_names, bg="#252526", fg="white", activebackground="#252526", activeforeground="white", highlightcolor="#252526", selectcolor="#252526")
        self.alternate_names_checkbox.grid(row=6, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))
        self.alternate_names_checkbox.config(command=self.on_alternate_names_checkbox_click)

        self.alternate_names_label = Label(self.container, text="Alternate Names: ", bg="#252526", fg="white")
        self.alternate_names_label.grid(row=7, column=0, sticky=NW, pady=(0, 10), padx=(0, 20))

        self.alternate_names_info_button = Button(self.container, text="?", bg="#252526", fg="white", width=1, height=1, command=lambda: messagebox.showinfo("Info", "Enter the alternate names separated by commas (e.g. Do, Re, ..) with the same order as the target notes. The total count of alternate names must be equal to the target notes count."), relief=FLAT, cursor="hand2", activebackground="#252526", activeforeground="white", bd=0)
        self.alternate_names_info_button.grid(row=7, column=1, sticky=NE, pady=(0, 10))

        self.alternate_names_entry = Text(self.container, bg="#2d2d30", fg="white", height=2, width=20, font=controller.default_font)
        self.alternate_names_entry.grid(row=8, column=0, sticky=NSEW, pady=(0, 10), columnspan=2)
        if self.has_alternate_names.get() == 0:
            self.alternate_names_label.grid_remove()
            self.alternate_names_entry.grid_remove()

        # random
        self.is_random = IntVar()
        self.random_checkbox = Checkbutton(self.container, text="Randomize Notes", variable=self.is_random, bg="#252526", fg="white", activebackground="#252526", activeforeground="white", highlightcolor="#252526", selectcolor="#252526")
        self.random_checkbox.grid(row=6, column=1, sticky=NW, pady=(0, 10), padx=(0, 20))


        # buttons
        save_button = Button(self.container, width=20,
                            command=self.on_save_button_click,
                            text="Save", bg="#2d2d30", fg="white", cursor="hand2")
        save_button.grid(row=9, column=0, sticky=NS, pady=(30, 0), padx=(0, 10))

        back_button = Button(self.container, width=20,
                            command=lambda: controller.show_frame("PracticeListPage"),
                            text="Back", bg="#2d2d30", fg="white", cursor="hand2")
        back_button.grid(row=9, column=1, sticky=NS, pady=(30, 0))

    def on_alternate_names_checkbox_click(self):
        # remove alternate names entry if alternate names checkbox is unchecked
        if self.has_alternate_names.get() == 0:
            self.alternate_names_label.grid_remove()
            self.alternate_names_info_button.grid_remove()
            self.alternate_names_entry.grid_remove()
        else:
            self.alternate_names_label.grid()
            self.alternate_names_info_button.grid()
            self.alternate_names_entry.grid()
    
    def on_save_button_click(self):
        # validate form
        # check if name is empty
        if not self.name_entry.get().strip():
            messagebox.showerror("Failed to Save", "Name cannot be empty")
            return
        # check if description is empty
        if not self.description_entry.get().strip():
            messagebox.showerror("Failed to Save", "Description cannot be empty")
            return
        # check if target notes is empty
        if not self.target_notes_entry.get(1.0, END).strip():
            messagebox.showerror("Failed to Save", "Target notes cannot be empty")
            return
        # check if alternate names is empty and alternate names checkbox is checked
        if self.has_alternate_names.get() and not self.alternate_names_entry.get(1.0, END).strip():
            messagebox.showerror("Failed to Save", "Alternate names cannot be empty")
            return
        # check if the target notes are in a form of a note followed by an octave number
        target_notes = [note.strip() for note in self.target_notes_entry.get(1.0, END).split(",") if note.strip()]
        if not all([(note[0] in pd.ALL_NOTES or note[:2] in pd.ALL_NOTES) and (note[1:].isdigit() or note[2:].isdigit()) for note in target_notes]):
            messagebox.showerror("Failed to Save", "Target notes must be in a form of a note followed by an octave number (e.g. A4, G#3, ..) and make sure it is in capital letter")
            return
        # check if alternate names count is not equal to target notes count, ignore empty strings as elements
        alternate_names = [note.strip() for note in self.alternate_names_entry.get(1.0, END).split(",") if note.strip()]
        if self.has_alternate_names.get() and len(target_notes) != len(alternate_names):
            messagebox.showerror("Failed to Save", "Alternate names count must be equal to target notes count")
            return
        # if alternate names is empty, use target notes as alternate names
        if not self.has_alternate_names.get() or len(alternate_names) == 0:
            alternate_names = target_notes

        # save practice
        practice = {
            "name": self.name_entry.get(),
            "description": self.description_entry.get(),
            "note_list": [{"note": target_notes[i], "alternate_name": alternate_names[i]} for i in range(len(target_notes))],
            "has_alternate_names": self.has_alternate_names.get(),
            "is_random": self.is_random.get()
        }
        if current_practice:
            practice_list[current_practice_idx] = practice
        else:
            practice_list.append(practice)
        with open("practice_list.json", "w") as f:
            json.dump(practice_list, f, indent=2)
        messagebox.showinfo("Success", "Practice saved!")
        self.controller.show_frame("PracticeListPage")

    
    def fill_form(self):
        self.clear_form()
        self.name_entry.insert(0, current_practice.get("name"))
        self.description_entry.insert(0, current_practice.get("description"))
        self.target_notes_entry.insert(1.0, ", ".join([note.get("note") for note in current_practice.get("note_list")]))
        self.has_alternate_names.set(current_practice.get("has_alternate_names"))
        self.alternate_names_entry.insert(1.0, ", ".join([note.get("alternate_name") for note in current_practice.get("note_list")]))
        self.on_alternate_names_checkbox_click()
        self.is_random.set(current_practice.get("is_random"))
    
    def clear_form(self):
        self.name_entry.delete(0, END)
        self.description_entry.delete(0, END)
        self.target_notes_entry.delete(1.0, END)
        self.has_alternate_names.set(0)
        self.alternate_names_entry.delete(1.0, END)
        self.on_alternate_names_checkbox_click()

# functions
def start_stream_thread():
    stream_thread.start()

def stop_stream_thread():
    if stream_thread.is_alive():
        stream_thread.terminate()
        stream_thread.join()

def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)

def get_random_list_idx(list, exclude_idx=None):
    idx = random.randint(0, len(list)-1)
    if exclude_idx != None:
        while idx == exclude_idx: # make sure the new idx is different from the exclude_idx
            idx = random.randint(0, len(list)-1)
    return idx

if __name__ == "__main__":
    stream_thread = StreamThread()
    stream_thread.daemon = True  # set Daemon thread

    app = App()
    app.mainloop()