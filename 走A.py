import json
import threading
import time
from ctypes import POINTER, c_ulong, Structure, c_ushort, c_short, c_long, windll, pointer, sizeof, Union

import requests
import wx
import wx.adv
import urllib3
import pyWinhook
import pythoncom

urllib3.disable_warnings()

PUL = POINTER(c_ulong)


def get_attack_speed():
    zhilianUrl = "https://127.0.0.1:2999/liveclientdata/activeplayer"
    try:
        with requests.get(zhilianUrl, verify=False) as r:
            if r.ok:
                lolJson = r.text
                data = json.loads(lolJson)
                return float(data["championStats"]["attackSpeed"])
            else:
                return None
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


# def get_mpos():
#     orig = POINT()
#     windll.user32.GetCursorPos(byref(orig))
#     return int(orig.x), int(orig.y)


# def set_mpos(pos):
#     x, y = pos
#     windll.user32.SetCursorPos(x, y)


# def move_click(pos, move_back=False):
#     origx, origy = get_mpos()
#     set_mpos(pos)
#     FInputs = Input * 2
#     extra = c_ulong(0)
#     ii_ = Input_I()
#     ii_.mi = MouseInput(0, 0, 0, 2, 0, pointer(extra))
#     ii2_ = Input_I()
#     ii2_.mi = MouseInput(0, 0, 0, 4, 0, pointer(extra))
#     x = FInputs((0, ii_), (0, ii2_))
#     windll.user32.SendInput(2, pointer(x), sizeof(x[0]))
#     if move_back:
#         set_mpos((origx, origy))
#         return origx, origy


def sendkey(scancode, pressed):
    FInputs = Input * 1
    extra = c_ulong(0)
    ii_ = Input_I()
    flag = 0x8
    ii_.ki = KeyBdInput(0, 0, flag, 0, pointer(extra))
    InputBox = FInputs((1, ii_))
    if scancode is None:
        return
    InputBox[0].ii.ki.wScan = scancode
    InputBox[0].ii.ki.dwFlags = 0x8

    if not (pressed):
        InputBox[0].ii.ki.dwFlags |= 0x2

    windll.user32.SendInput(1, pointer(InputBox), sizeof(InputBox[0]))


class KeyBdInput(Structure):
    _fields_ = [("wVk", c_ushort),
                ("wScan", c_ushort),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", PUL)]


class HardwareInput(Structure):
    _fields_ = [("uMsg", c_ulong),
                ("wParamL", c_short),
                ("wParamH", c_ushort)]


class MouseInput(Structure):
    _fields_ = [("dx", c_long),
                ("dy", c_long),
                ("mouseData", c_ulong),
                ("dwFlags", c_ulong),
                ("time", c_ulong),
                ("dwExtraInfo", PUL)]


class Input_I(Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]


class Input(Structure):
    _fields_ = [("type", c_ulong),
                ("ii", Input_I)]


class POINT(Structure):
    _fields_ = [("x", c_ulong),
                ("y", c_ulong)]


class TaskBarIcon(wx.adv.TaskBarIcon):
    ID_About = wx.NewIdRef()
    ID_Close = wx.NewIdRef()

    def __init__(self, frame):
        wx.adv.TaskBarIcon.__init__(self)
        self.frame = frame
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_task_bar_left_click)
        self.Bind(wx.EVT_MENU, self.on_about, id=self.ID_About)
        self.Bind(wx.EVT_MENU, self.on_close, id=self.ID_Close)

    def on_task_bar_left_click(self, event):
        if self.frame.IsIconized():
            self.frame.Iconize(False)
        if not self.frame.IsShown():
            self.frame.Show(True)
        self.frame.Raise()

    def on_about(self, event):
        wx.MessageBox("Test")

    def on_close(self, event):
        self.Destroy()
        self.frame.Destroy()

    def create_popup_menu(self):
        menu = wx.Menu()
        menu.Append(self.ID_About, '使用幫助')
        menu.Append(self.ID_Close, '退出')
        return menu


class MainWindow(wx.Frame):
    minTime = 0.1
    onlyLoL = True
    currentKey = "Capital"
    GongSu = 0.7
    QianYao = 0.35
    YDBC = 0.0
    dc = 1.0 / GongSu
    qy = dc * QianYao
    hy = dc - qy + YDBC

    press_the_trigger_button = False
    
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, pos=wx.DefaultPosition, style=wx.DEFAULT_FRAME_STYLE ^ (
                wx.MAXIMIZE_BOX | wx.SYSTEM_MENU) | wx.STAY_ON_TOP, size=(210, 180))

        self.SetBackgroundColour("#ffffff")
        self.taskBarIcon = TaskBarIcon(self)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.isPause = False
        self.start_setting = False

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.text2 = wx.StaticText(self, name="aa", label="前摇", size=(40, -1), style=wx.ALIGN_CENTER)
        self.text_num2 = wx.StaticText(self, name="aa", label=str(self.QianYao), size=(60, -1), style=wx.ALIGN_CENTER)
        self.text2.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text_num2.SetFont(wx.Font(20, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.text2.SetForegroundColour('#000000')
        self.text_num2.SetForegroundColour('#0000FF')
        self.button_up2 = wx.Button(self, name="up2", label="→", size=(30, 30))
        self.button_down2 = wx.Button(self, name="down2", label="←", size=(30, 30))
        self.Bind(wx.EVT_BUTTON, self.on_click, self.button_up2)
        self.Bind(wx.EVT_BUTTON, self.on_click, self.button_down2)
        self.sizer2.Add(self.text2, flag=wx.ALIGN_CENTER)
        self.sizer2.Add(self.text_num2, flag=wx.ALIGN_CENTER)
        self.sizer2.Add(self.button_down2, flag=wx.ALIGN_CENTER)
        self.sizer2.Add(self.button_up2, flag=wx.ALIGN_CENTER)

        self.text3 = wx.StaticText(self, name="aa", label="移補", size=(40, -1), style=wx.ALIGN_CENTER)
        self.text_num3 = wx.StaticText(self, name="aa", label=str(self.YDBC), size=(60, -1), style=wx.ALIGN_CENTER)
        self.text3.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text_num3.SetFont(wx.Font(20, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.text3.SetForegroundColour('#000000')
        self.text_num3.SetForegroundColour('#000000')
        self.button_up3 = wx.Button(self, name="up3", label="+", size=(30, 30))
        self.button_down3 = wx.Button(self, name="down3", label="-", size=(30, 30))
        self.Bind(wx.EVT_BUTTON, self.on_click, self.button_up3)
        self.Bind(wx.EVT_BUTTON, self.on_click, self.button_down3)
        self.sizer3.Add(self.text3, flag=wx.ALIGN_CENTER)
        self.sizer3.Add(self.text_num3, flag=wx.ALIGN_CENTER)
        self.sizer3.Add(self.button_down3, flag=wx.ALIGN_CENTER)
        self.sizer3.Add(self.button_up3, flag=wx.ALIGN_CENTER)

        self.button_start = wx.Button(self, name="start", label="開", size=(40, 30))
        self.button_stop = wx.Button(self, name="stop", label="關", size=(40, 30))
        self.button_setting = wx.Button(self, name="setting", label="設觸發鍵", size=(80, 30))
        self.Bind(wx.EVT_BUTTON, self.on_click, self.button_start)
        self.Bind(wx.EVT_BUTTON, self.on_click, self.button_stop)
        self.Bind(wx.EVT_BUTTON, self.on_click, self.button_setting)
        self.sizer4.Add(self.button_start, flag=wx.ALIGN_CENTER)
        self.sizer4.Add(self.button_stop, flag=wx.ALIGN_CENTER)
        self.sizer4.Add(self.button_setting, flag=wx.ALIGN_CENTER)

        self.message_text = wx.StaticText(self, name="aa", label="已啟動,按住[" + self.currentKey + "]走A\n進入遊戲後自動獲取攻速")
        self.message_text.SetForegroundColour('#000000')
        self.sizer5.Add(self.message_text)

        self.sizer.Add(self.sizer2)
        self.sizer.Add(self.sizer3)
        self.sizer.Add(self.sizer4)
        self.sizer.Add(self.sizer5)

        self.SetSizer(self.sizer)
        self.Show(True)

        self.thread_key = threading.Thread(target=self.action)
        self.thread_action = threading.Thread(target=self.key_listener)
        self.thread_listenerAttackSpeed = threading.Thread(target=self.listener_attack_speed)
        self.thread_listenerAttackSpeed.daemon = True
        self.thread_key.daemon = True
        self.thread_action.daemon = True
        self.thread_listenerAttackSpeed.start()
        self.thread_key.start()
        self.thread_action.start()

    def on_key_down(self, event):
        if event.Key == self.currentKey:
            self.press_the_trigger_button = True
            if self.onlyLoL and not self.isPause:
                sendkey(0x2e, 1)
            return self.isPause
        elif event.Key == "Right":
            self.update_number(self.text_num2, True, 0, 1, 0.01)
            self.Iconize(False)
            return self.isPause
        elif event.Key == "Left":
            self.update_number(self.text_num2, False, 0, 1, 0.01)
            self.Iconize(False)
            return self.isPause
        elif event.Key == "Prior":
            self.isPause = False
            self.SetTransparent(255)
            self.message_text.Label = "已啟動,按住[" + self.currentKey + "]走A"
            self.Iconize(False)
            return False
        elif event.Key == "Next":
            self.isPause = True
            self.SetTransparent(90)
            self.message_text.Label = "已關閉"
            self.Iconize(False)
            return False
        elif event.Key == "Insert":
            self.start_setting = True
            self.currentKey = ""
            self.message_text.Label = "按任意鍵完成綁定"
            self.Iconize(False)
            return False
        elif not self.IsIconized() and event.Key == "Escape":
            self.Iconize(True)
            return False
        elif self.start_setting:
            self.currentKey = event.Key
            self.start_setting = False
            self.message_text.Label = "已經綁定到：" + self.currentKey
            self.Iconize(False)
            return False
        return True

    def on_key_up(self, event):
        if event.Key == self.currentKey:
            self.press_the_trigger_button = False
            if self.onlyLoL:
                sendkey(0x2e, 0)
            return self.isPause
        return True

    def action(self):
        while True:
            if self.press_the_trigger_button and not self.isPause:
                self.click(0x2c, self.qy)
                self.click(0x2d, self.hy)
            else:
                time.sleep(0.01)

    def click(self, key, click_time):
        while click_time > self.minTime and self.press_the_trigger_button:
            process_time = time.time()
            sendkey(key, 1)
            sendkey(key, 0)
            time.sleep(self.minTime)
            click_time = click_time - (time.time() - process_time)
        if self.press_the_trigger_button and click_time >= 0:
            sendkey(key, 1)
            sendkey(key, 0)
            time.sleep(click_time)

    def key_listener(self, ):
        hm = pyWinhook.HookManager()
        hm.KeyDown = self.on_key_down
        hm.KeyUp = self.on_key_up
        hm.HookKeyboard()
        hm.HookMouse()
        pythoncom.PumpMessages()

    def listener_attack_speed(self, ):
        while True:
            time.sleep(0.2)
            speed = get_attack_speed()
            print(speed)
            if speed is None:
                continue
            if speed <= 0:
                continue
            if self.GongSu == speed:
                continue
            self.GongSu = speed
            self.dc = 1.0 / self.GongSu
            self.qy = self.dc * self.QianYao
            self.hy = self.dc - self.qy + self.YDBC

    def on_close(self, event):
        self.Iconize(True)

    def on_click(self, event):
        name = event.GetEventObject().GetName()
        
        action_map = {
            "up2": (self.update_number, self.text_num2, True, 0.1, 0.9, 0.05),
            "down2": (self.update_number, self.text_num2, False, 0.1, 0.9, 0.05),
            "up3": (self.update_number, self.text_num3, True, 0.0, 1.0, 0.01),
            "down3": (self.update_number, self.text_num3, False, 0.0, 1.0, 0.01),
        }
        
        if action := action_map.get(name):
            function, *args = action
            function(*args)
        else:
            if name == "start":
                self.isPause = False
                self.SetTransparent(255)
                self.message_text.Label = "已啟動,按住[" + self.currentKey + "]走A"
            elif name == "stop":
                self.isPause = True
                self.SetTransparent(90)
                self.message_text.Label = "已關閉"
            elif name == "setting":
                self.start_setting = True
                self.currentKey = ""
                self.message_text.Label = "按任意鍵完成綁定"

    def update_number(self, who, isUp, min, max, min_diff):
        if isUp:
            num = float(who.Label) + min_diff
        else:
            num = float(who.Label) - min_diff
        num = round(num, 2)
        if num < min:
            num = min
        if num > max:
            num = max
        if who == self.text_num2:
            self.QianYao = num
        elif who == self.text_num3:
            self.YDBC = num
        self.dc = 1.0 / self.GongSu
        self.qy = self.dc * self.QianYao
        self.hy = self.dc - self.qy + self.YDBC
        num = str(num)
        if len(num) > 3:
            num = num[0:4]
        who.SetLabel(num)

if __name__ == "__main__":
    app = wx.App(False)
    ui = MainWindow(None, "刀！")
    ui.Centre()
    app.MainLoop()