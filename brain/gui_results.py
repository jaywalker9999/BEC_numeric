import tkinter as tk
import tkinter.font as font
from tkinter import messagebox
from tkinter.filedialog import asksaveasfilename, askopenfilename

import matplotlib as mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
import matplotlib.pyplot as plt

import numpy as np
from .data_manager import DataManager

class ResultsApp(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.data_manager = DataManager()
        self.animation_is_playing = False
        self.step_forward = False
        self.step_backward = False

        self.current_animation_frame = 0
        self.last_animation_frame = 0
        self.animation_delay = 1

        self.E = []
        self.Nabla = []
        self.L = []
        self.t = []

        self.padx = 5
        self.pady = 5

        self.init_frames()
        self.init_top_left()
        self.init_top_right()

        self.init_bottom()

        # self.initAnimation()

    def __del__(self):
        self.data_manager.__del__()

    def init_frames(self):
        self.topLevelFrame = tk.Frame(self.parent)
        self.topLevelFrame.grid()

        self.top_left = tk.Frame(self.topLevelFrame, width=300, height=300, padx=self.padx, pady=self.pady, relief=tk.GROOVE, borderwidth=3)
        self.top_right = tk.LabelFrame(self.topLevelFrame, text='File Parameters', labelanchor='nw', width=300, height=300, padx=self.padx, pady=self.pady, relief=tk.GROOVE, borderwidth=3)

        self.bottom = tk.Frame(self.topLevelFrame, width=300, height=300, padx=self.padx, pady=self.pady, relief=tk.GROOVE, borderwidth=3)
        

        # layout all of the main containers
        # self.parent.grid_rowconfigure(1, weight=1)
        # self.parent.grid_columnconfigure(0, weight=1)

        self.top_left.grid(row=0, column=0, columnspan=2, padx=self.padx, pady=self.pady, sticky='')
        self.top_right.grid(row=0, column=2, padx=self.padx, pady=self.pady, sticky='')

        self.bottom.grid(row=1, column=0, columnspan=3, padx=self.padx, pady=self.pady, sticky='')

    def init_top_left(self):
        padY = 20

        filename_label = tk.Label(self.top_left, text="Datei")
        self.filename_sv = tk.StringVar(value="test")
        self.filename_entry = tk.Entry(self.top_left, width=45, justify=tk.RIGHT, textvariable=self.filename_sv, state=tk.DISABLED)

        self.open_file_button = tk.Button(self.top_left, command=self.openFile, text='Öffne Datei')
        self.close_file_button = tk.Button(self.top_left, command=self.closeFile, text='Schließe Datei')

        self.save_as_button = tk.Button(self.top_left, command=self.saveFrames, text='Speichere als .mp4 Datei')

        self.play_button = tk.Button(self.top_left, command = self.continueAnimation, text='play |>')
        self.pause_button = tk.Button(self.top_left, command = self.pauseAnimation, text='pause ||')
        self.step_forward_button = tk.Button(self.top_left, command = self.stepForward, text='step >>')
        self.step_backward_button = tk.Button(self.top_left, command = self.stepBackward, text='step <<')

        skip_frames_label = tk.Label(self.top_left, text='Number of Frames skipped on each screen refresh.\nA high value increases playback speed.')
        self.skip_frames_iv = tk.IntVar(value=0)
        self.skip_frames_scale = tk.Scale(self.top_left, from_=0, to_=15, resolution=1, tickinterval=5, orient=tk.HORIZONTAL, variable=self.skip_frames_iv, length=200)


        filename_label.grid(row=0, column=0, columnspan=4, pady=5)
        self.filename_entry.grid(row=1, column=0, columnspan=5, pady=padY)
        self.open_file_button.grid(row=1, column=5, pady=padY)
        self.close_file_button.grid(row=1, column=6, pady=padY)

        self.save_as_button.grid(row=2, column=0, columnspan=4, pady=padY)

        self.play_button.grid(row=3, column=0, pady=padY)
        self.pause_button.grid(row=3, column=1, pady=padY)
        self.step_backward_button.grid(row=3, column=2, pady=padY)
        self.step_forward_button.grid(row=3, column=3, pady=padY)

        skip_frames_label.grid(row=4, column=0, columnspan=4, pady=padY)
        self.skip_frames_scale.grid(row=4, column=4, columnspan=2, pady=padY)

    def init_top_right(self):
        self.parameters_text = tk.Text(self.top_right, width=60, height=20)
        self.parameters_text.grid(row=0, column=0, sticky="nsew")

        scrollb = tk.Scrollbar(self.top_right, command=self.parameters_text.yview)
        scrollb.grid(row=0, column=1, sticky='nsew')
        self.parameters_text['yscrollcommand'] = scrollb.set

    def init_bottom(self):
        self.fig, (self.ax0, self.ax1, self.ax2) = plt.subplots(1,3,figsize=(12,4))

        self.fig.tight_layout()

        shape = (256, 256)
        data = np.random.rand(*shape)
        self.im0 = self.ax0.imshow(data, cmap='jet', animated=True, vmin=0, vmax=1)
        self.im1 = self.ax1.imshow(data, cmap='jet', animated=True, vmin=0, vmax=1)

        self.pl1, = self.ax2.plot([0], [0])
        self.pl2, = self.ax2.plot([0], [0])
        self.pl3, = self.ax2.plot([0], [0])

        self.V_canvas = FigureCanvasTkAgg(self.fig, master=self.bottom)  # A tk.DrawingArea.
        self.V_canvas.draw()
        self.V_canvas.get_tk_widget().grid(row=0, column=0)

    def openFile(self):
        filetypes = [('hdf5 database files', '*.hdf5'), ('All files', '*')]
        filename = askopenfilename(title='Open..', defaultextension='.hdf5', filetypes=filetypes)
        if filename:
            self.filename_sv.set(filename)
            self.data_manager.filename = filename

            # Giving out information about loading the file...
            self.clearParameterWidget()
            self.parameters_text.insert(tk.END, '\nTrying to load the file now.\n')
            self.parameters_text.insert(tk.END, 'This might take a while, depending on the filesize.\n')
            try:
                self.parent.after(0, self.data_manager.loadFile())
                self.open_file_button['state'] = tk.DISABLED
                # set up plots
                if not self.data_manager.are_observables_calculated():
                    self.parameters_text.insert(tk.END, '\nThe observables have not yet been calculated!\nThis will take a bit.\nPlease do not close the window, it possibly corrupts the file.\n')
                self.E, self.L, self.Nabla, self.t = self.data_manager.getObservables()
                
                y_min = np.min((np.min(self.E), np.min(self.L), np.min(self.Nabla)))
                y_max = np.max((np.max(self.E), np.max(self.L), np.max(self.Nabla)))

                _, attributes_last_frame = self.data_manager.getDset(self.data_manager.getLastKey())
                self.ax2.set_xlim(0, attributes_last_frame['t'])
                self.ax2.set_ylim(y_min-10, y_max+10)

                self.last_animation_frame = int(self.data_manager.getLastKey())
                self.resetParameterWidget()

            except Exception as inst:
                messagebox.showerror("ERROR: {}".format(type(inst)), inst)

            # start the animation
            self.initAnimation()
            self.animation_is_playing = True
        
    def closeFile(self):
        self.animation_is_playing = False
        self.data_manager.closeFile()
        self.open_file_button['state'] = tk.NORMAL
        print('close file')

    def saveFrames(self):
        print("[INFO] Saving the animation in .mp4 format, this will take a while.")
        try:
            filetypes = [('mp4 video files', '*.mp4'), ('All files', '*')]
            f = asksaveasfilename(title='Save as..', defaultextension='.mp4', filetypes=filetypes)
            fps = 40
            if f:
                self.data_manager.saveFrames(f, fps=fps, dpi=500)
        except Exception as inst:
            messagebox.showerror("ERROR: {}".format(type(inst)), inst)

    def initAnimation(self):
        self.current_animation_frame = 0
        self.animation = animation.FuncAnimation(self.fig, self.updateAnimation, interval=self.animation_delay, blit=True)
        self.V_canvas.draw()

    def updateAnimation(self, i):
        if self.animation_is_playing or self.step_forward or self.step_backward:
            if self.step_forward or self.animation_is_playing:
                self.current_animation_frame += 1 + self.skip_frames_iv.get()
            elif self.step_backward:
                self.current_animation_frame -= 1 + self.skip_frames_iv.get()

            # making sure we only get valid values for the frame index
            if self.current_animation_frame > self.last_animation_frame:
                self.current_animation_frame = 0
            elif self.current_animation_frame < 0:
                self.current_animation_frame = self.last_animation_frame
            # print("current animation frame", self.current_animation_frame)
            
            # make the key for the data manager frame
            if self.current_animation_frame > self.last_animation_frame:
                key = self.data_manager.makeKey(self.last_animation_frame)
            else:
                key = self.data_manager.makeKey(self.current_animation_frame)
            psi_array, _ = self.data_manager.getDset(key)

            # tx.set_text("Frame {} of {}\nn = {}\nt = {:2.3f}".format(i, lastKey+endingFrameDelay*fps, attributes['n'],  attributes['t']))
            self.im0.set_data(np.abs(psi_array)**2)
            self.im1.set_data(np.angle(psi_array))

            vmin = np.min(np.abs(psi_array)**2)
            vmax = np.max(np.abs(psi_array)**2)
            self.im0.set_clim(vmin,vmax)

            # observables#
            key = int(key)
            self.pl1.set_data(self.t[:key], self.E[:key])
            self.pl2.set_data(self.t[:key], self.L[:key])
            self.pl3.set_data(self.t[:key], self.Nabla[:key])

            self.step_backward = False
            self.step_forward = False

        return self.im0, self.im1, self.pl1, self.pl2, self.pl3

    def continueAnimation(self):
        self.animation_is_playing = True
    
    def pauseAnimation(self):
        self.animation_is_playing = False

    def stepForward(self):
        self.step_forward = True

    def stepBackward(self):
        self.step_backward = True

    def resetParameterWidget(self):
        self.parameters_text.delete("@0,0", tk.END)
        self.parameters_text.insert("@0,0", self.data_manager.returnInfo())

    def clearParameterWidget(self):
        self.parameters_text.delete("@0,0", tk.END)