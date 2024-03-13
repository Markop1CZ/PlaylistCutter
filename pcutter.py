import tkinter
import os
import math
from tkinter import filedialog
from idlelib.tooltip import OnHoverTooltipBase
from PIL import Image, ImageDraw, ImageTk
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
from pydub.utils import mediainfo

class VerticalScrolledFrame(tkinter.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    """
    def __init__(self, parent, *args, **kw):
        tkinter.Frame.__init__(self, parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tkinter.Scrollbar(self, orient=tkinter.VERTICAL)
        vscrollbar.pack(fill=tkinter.Y, side=tkinter.RIGHT, expand=False)
        canvas = tkinter.Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tkinter.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tkinter.NW)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.interior.bind_all("<MouseWheel>", _on_mousewheel)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)

PLAYBACK = None
music_file_ext = ["mp3", "wav", "flac"]

def util_callback_sv(master, default_val, update_func):
    v = tkinter.StringVar(master, default_val)
    v.trace("w", lambda n,i,m,v=v: update_func())

    return v

class SimpleHovertip(OnHoverTooltipBase):
    def __init__(self, anchor_widget, text, hover_delay=1000):
        super(SimpleHovertip, self).__init__(anchor_widget, hover_delay=hover_delay)
        self.text = text

    def showcontents(self):
        self.r_text = tkinter.StringVar(self.tipwindow, value=self.text)
        label = tkinter.Label(self.tipwindow, textvariable=self.r_text, justify=tkinter.LEFT,
                      background="#ffffe0", relief=tkinter.SOLID, borderwidth=1)
        label.pack()

class PlaylistSong:
    def __init__(self, filename):
        self.bar_count = 1024
        self.db_ceiling = 60
        self.wave_w = 512
        self.wave_h = 96
        
        self.filename = filename

        self.audio = AudioSegment.from_file(self.filename, os.path.splitext(self.filename)[1][1:])
        self.info = mediainfo(self.filename)

        self.calculate_peaks()
        self.generate_waveform_image()

    def edit_song(self, start, dur, fade_in, fade_out):
        s = math.floor(start*1000)
        d = math.floor(dur*1000)
        fi = math.floor(fade_in*1000)
        fo = math.floor(fade_out*1000)

        output = self.audio[s:s+d]

        if fi > 0:
            output = output.fade_in(fi)
        if fo > 0:
            output = output.fade_out(fo)

        return output

    def format_name(self):
        if "TAG" in self.info:
            t = self.info["TAG"]
            if "title" in t and "artist" in t:
                return t["artist"] + " - " + t["title"]

            elif "title" in t:
                return t["title"]
            
        return os.path.splitext(os.path.basename(self.filename))[0]

    def calculate_peaks(self):
        chunk_length = len(self.audio) / self.bar_count

        loudness_of_chunks = [self.audio[i * chunk_length: (i + 1) * chunk_length].rms for i in range(self.bar_count)]

        max_rms = max(loudness_of_chunks) * 1.00

        self.peaks = [int((loudness / max_rms) * self.db_ceiling) for loudness in loudness_of_chunks]

    def generate_waveform_image(self):
        w = self.wave_w
        h = self.wave_h
        
        self.wave_img = Image.new('RGB', (w, h), '#f5f5f5')
        draw = ImageDraw.Draw(self.wave_img)
        
        ymax = max(self.peaks)
        for i, value in enumerate(self.peaks, start=0):
            x = (i/self.bar_count) * w
            ym = (value/ymax) * (h/2)
            y1 = (h/2)+ym
            y2 = (h/2)-ym
            
            draw.line(((x, y1), (x, y2)), "red", width=0)

class PlayList:
    def __init__(self, filepath):
        self.path = filepath
        self.songs = []
        
        for f in os.listdir(filepath):
            n, ext = os.path.splitext(f)
            
            if not ext[1:].lower() in music_file_ext:
                print(f"playlist: unsupported file format: {f}")

            print(f"playlist: loading {f}")
            self.songs.append(PlaylistSong(os.path.join(self.path, f)))

    def get_songs(self):
        return self.songs

## gui
class SongEditPanel:
    def __init__(self, parent_frame, gui_song, update_func):
        self.gui_song = gui_song
        self.frame = tkinter.Frame(parent_frame)

        self.ps_frame = tkinter.Frame(self.frame)
        self.play_btn = tkinter.Button(self.ps_frame, text="Play", command=self.gui_song.gui_play)
        self.play_btn.pack(side=tkinter.LEFT, padx=5, pady=5)

        self.stop_btn = tkinter.Button(self.ps_frame, text="Stop", command=self.gui_song.gui_stop_play)
        self.stop_btn.pack(side=tkinter.LEFT, padx=5, pady=5)

        self.stop_btn = tkinter.Button(self.ps_frame, text="At start", command=self.gui_song.time_start_at_start)
        self.stop_btn.pack(side=tkinter.LEFT, padx=5, pady=5)

        self.ps_frame.pack()

        self.opt_frame = tkinter.Frame(self.frame)
        self.fi_label = tkinter.Label(self.opt_frame, text="Fade in:")
        self.fi_entry = tkinter.Entry(self.opt_frame, textvariable=util_callback_sv(self.opt_frame, "3", update_func))

        self.fo_label = tkinter.Label(self.opt_frame, text="Fade out:")
        self.fo_entry = tkinter.Entry(self.opt_frame, textvariable=util_callback_sv(self.opt_frame, "3", update_func))

        self.dur_label = tkinter.Label(self.opt_frame, text="Duration:")
        self.dur_entry = tkinter.Entry(self.opt_frame, textvariable=util_callback_sv(self.opt_frame, "30", update_func))

        for e in [self.fi_entry, self.fo_entry, self.dur_entry]:
            e.bind("<Key>", update_func)

        self.dur_label.grid(row=1, column=1)
        self.dur_entry.grid(row=1, column=2)
        self.fi_label.grid(row=2, column=1)
        self.fi_entry.grid(row=2, column=2)
        self.fo_label.grid(row=3, column=1)
        self.fo_entry.grid(row=3, column=2)

        self.opt_frame.pack()

    def get_entry_float_safe(self, e):
        val = e.get()
        try:
            val = float(val)
            return val
        except:
            print("error parsing", val)
            return 0.0

    def get_region_duration(self):
        return self.get_entry_float_safe(self.dur_entry)

    def get_fade_in(self):
        return self.get_entry_float_safe(self.fi_entry)

    def get_fade_out(self):
        return self.get_entry_float_safe(self.fo_entry)

    def pack(self):
        self.frame.pack()
    
class GuiSongPanel:
    def __init__(self, song, parent):
        self.song = song
        
        self.frame = tkinter.Frame(parent)
        self.label = tkinter.Label(self.frame, text=self.song.format_name())
        self.label.pack()

        self.img_frame = tkinter.Frame(self.frame)
        self.control_frame = tkinter.Frame(self.frame)

        self.edit_w = self.song.wave_img.width()
        self.edit_h = self.song.wave_img.height()

        self.edit_canvas = tkinter.Canvas(self.img_frame, width=self.edit_w, height=self.edit_h)    
        self.edit_canvas.bind("<Motion>", self.canvas_on_hover)
        self.edit_canvas.bind("<Button-1>", self.event_update_time_start)
        self.edit_canvas.bind("<Button-3>", self.gui_play_from_event)
        self.edit_canvas.pack(side=tkinter.BOTTOM, fill="both", expand="yes")

        self.edit_canvas.create_image(0, 0, anchor=tkinter.NW, image=self.song.wave_img)
        self.edit_lines = []

        self.canvas_hover = SimpleHovertip(self.edit_canvas, "00:00", 0)

        self.song_edit = SongEditPanel(self.control_frame, self, self.update_canvas)
        self.song_edit.pack()

        self.img_frame.pack(side=tkinter.LEFT, padx=5, pady=10)
        self.control_frame.pack(side=tkinter.LEFT, padx=5, pady=10)

        self.time_start = 0
        self.update_canvas()

    def update_canvas(self, evt=None):
        x = (self.time_start/self.song.audio.duration_seconds)*self.edit_w
        duration = self.song_edit.get_region_duration()
        x1 = x + (duration/self.song.audio.duration_seconds)*self.edit_w

        for l in self.edit_lines:
            self.edit_canvas.delete(l)

        for xcoord in [x, x1]:
            self.edit_lines.append(self.edit_canvas.create_line(xcoord, 0, xcoord, self.edit_h, fill="blue", width=2.0))

    def event_update_time_start(self, evt):
        self.update_time_start(evt.x)

    def time_start_at_start(self):
        self.update_time_start(0)

    def update_time_start(self, x):
        self.gui_stop_play()
        t = (x/self.edit_w)*self.song.audio.duration_seconds
        self.time_start = t

        print("song={0} start={1} duration={2} fadein={3} fadeout={4}".format(self.song.format_name(), "{0:02d}:{1:02d}".format(int(math.floor(t/60)), int(t%60)), self.song_edit.get_region_duration(), self.song_edit.get_fade_in(), self.song_edit.get_fade_out()))

        self.update_canvas()

    def canvas_on_hover(self, evt):
        t = (evt.x/self.edit_w)*self.song.audio.duration_seconds
        self.canvas_hover.r_text.set("{0:02d}:{1:02d}".format(int(math.floor(t/60)), int(t%60)))

    def gui_play_from_event(self, evt):
        global PLAYBACK
        self.gui_stop_play()

        t = (evt.x/self.edit_w)*self.song.audio.duration_seconds
        end = self.song_edit.get_region_duration()
        if t >= self.time_start and t <= self.time_start + end:
            PLAYBACK = _play_with_simpleaudio(self.song.edit_song(t, end-(t-self.time_start), 0, 0))

    def gui_play(self):
        global PLAYBACK
        self.gui_stop_play()
    
        s = self.song.edit_song(self.time_start, self.song_edit.get_region_duration(), self.song_edit.get_fade_in(), self.song_edit.get_fade_out())
        PLAYBACK = _play_with_simpleaudio(s)

    def gui_stop_play(self):
        global PLAYBACK
        if not PLAYBACK is None:
            PLAYBACK.stop()

    def pack(self):
        self.frame.pack()

    def export(self, folder="output"):
        output_folder = os.path.join(os.path.dirname(self.song.filename), folder)
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        s = self.song.edit_song(self.time_start, self.song_edit.get_region_duration(), self.song_edit.get_fade_in(), self.song_edit.get_fade_out())
        filename = os.path.splitext(os.path.basename(self.song.filename))[0] + ".mp3"
        
        s.export(os.path.join(output_folder, filename))
        
class GuiSongPlaylist:
    def __init__(self, songs, parent):
        self.songs_audio = songs
        self.songs = []

        self.frame = VerticalScrolledFrame(parent)
        
        for s in self.songs_audio:
            gp = GuiSongPanel(s, self.frame.interior)
            self.songs.append(gp)

            gp.pack()

        self.export_btn = tkinter.Button(self.frame, text="Export", command=self.export_all)
        self.export_btn.pack()

    def export_all(self):
        for s in self.songs:
            s.export()

    def pack(self):
        self.frame.pack(fill=tkinter.Y, expand=True)

directory = filedialog.askdirectory()
pl = PlayList(directory)

w = tkinter.Tk()

g = GuiSongPlaylist(pl.get_songs(), w)
g.pack()

w.mainloop()