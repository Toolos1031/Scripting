from win32 import win32gui
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import PySimpleGUI as sg
import time
from pynput.keyboard import Key, Controller
from threading import Thread


# Get default audio device using PyCAW
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# Some inputs
names = ["Spotify", "Advertisement"]
list = []
splittedlist = []
skiplist = ["Sheeran", "Ava", "Styles", "Despacito"]
keyboard = Controller()


# Call to determine whether its running
running = False
ads = False

# Set a simple layout
layout = [[sg.Text(f"Program is {running}", key="PROGRAM")],
          [sg.Text("", key="Print")],
          [sg.Text("", key="ADS")],
          [sg.Text('Ad Name', size=(15, 1)), sg.InputText()],
          [sg.Button("Add")],
          [sg.Text("", key="Empty")],
          [sg.Text("Skippable name", size=(15, 1)), sg.InputText()],
          [sg.Button("Add skippable Name")],
          [sg.Text("", key="Song")],
          [sg.Button(button) for button in ("Start", "Kill")]]

# Set up a window
window = sg.Window("Spotify ads silencer", layout, finalize=True, size=(300, 300), return_keyboard_events=True)
runner = window["PROGRAM"]
muter = window["Print"]
ad = window["ADS"]
empty = window["Empty"]
song = window["Song"]

# Better muting function
def mute_lists():
    a = 0 # variable resets everytime
    for i in names:
        try: # try to trigger an error
            hwnd = win32gui.FindWindow(None, r'{}'.format(i))
            win32gui.GetWindowRect(hwnd)
        except:
            a = a + 1 # for every name that triggers an error add 1
            if a == len(names): # if number of names that triggers errors matches the overall number of names - MUTE
                volume.SetMute(0, None)
            ads = False
            ad.update(f"Are ads playing?: {ads}")
        else:
            volume.SetMute(1, None)
            ads = True
            ad.update(f"Are ads playing?: {ads}")

# Muting function
def mute():
    try:
        hwnd = win32gui.FindWindow(None, r'Advertisement')
        win32gui.GetWindowRect(hwnd)
    except:
        try:
            hwnd = win32gui.FindWindow(None, r'Spotify')
            win32gui.GetWindowRect(hwnd)
        except:
            volume.SetMute(0, None)
            ads = False
            ad.update(f"Are ads playing?: {ads}")
        else:
            volume.SetMute(1, None)
            ads = True
            ad.update(f"Are ads playing?: {ads}")
    else:
        volume.SetMute(1, None)
        ads = True
        ad.update(f"Are ads playing?: {ads}")

# Function for window listing
def winEnumHandler(hwnd, ctx):
    if win32gui.IsWindowVisible(hwnd): # if the window is visible
        list.append(win32gui.GetWindowText(hwnd)) # add it to the list of visible windows

# Better function for skipping
def to_skip():
    win32gui.EnumWindows(winEnumHandler, None)
    splittedlist = [word for line in list for word in line.split()] # split names of windows into single words
    list.clear()
    skiplist_copy = skiplist[:]

    for i in splittedlist:
        for j in skiplist_copy:
            if i == j: # compare both lists and look for same items
                keyboard.press(Key.media_next)
                keyboard.release(Key.media_next)
                skiplist_copy.remove(j)
                time.sleep(1)
                break

while True:

    event, values = window.read(timeout=1000)

    if event == sg.WINDOW_CLOSED:
        volume.SetMute(0, None)
        break
    elif event == "Start":
        muting = "Started"
        running = True
        runner.update(f"Program is {running}")
        muter.update(f"Muting {muting}")
    elif event == "Kill":
        running = False
        muting = "Stopped"
        volume.SetMute(0, None)
        ads = "Program Abrupted"
        muter.update(f"Muting {muting}")
        runner.update(f"Program is {running}")
        ad.update(f"Are ads playing?: {ads}")
    elif event == "Add":
        if values[0] != "":
            names.append(values[0])
            empty.update(f"{values[0]} - Added")
        else:
            empty.update("Insert a non empty value")
    elif event == "Add skippable Name":
        if values[1] != "":
            skiplist.append(values[1])
            song.update(f"{values[1]} - Added")
        else:
            song.update("Insert a non empty value")
    elif event == sg.TIMEOUT_EVENT and running:
        runner.update(f"Program is {running}")
        to_skip()
        mute()

window.close()
