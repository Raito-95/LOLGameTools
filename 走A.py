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
    url = "https://127.0.0.1:2999/liveclientdata/activeplayer"
    try:
        with requests.get(url, verify=False) as r:
            if r.ok:
                lolJson = r.text
                data = json.loads(lolJson)
                return float(data["championStats"]["attackSpeed"])
            else:
                return None
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


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


class MainWindow(wx.Frame):
    minTime = 0.1
    onlyLoL = True
    currentKey = "Capital"
    attackSpeed = 0.7
    windupPercent = 0.35
    windupModifier = 0.0
    attackTime = 1.0 / attackSpeed
    windupTime = attackTime * windupPercent
    timeBetweenAttacks = attackTime - windupTime + windupModifier

    pressTheTriggerButton = False
    
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, pos=wx.DefaultPosition, style=wx.DEFAULT_FRAME_STYLE ^ (
                wx.MAXIMIZE_BOX | wx.SYSTEM_MENU) | wx.STAY_ON_TOP, size=(210, 180))

        self.SetBackgroundColour("#ffffff")
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.is_pause = False
        self.start_setting = False

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.text2 = wx.StaticText(self, name="aa", label="前摇", size=(40, -1), style=wx.ALIGN_CENTER)
        self.text_num2 = wx.StaticText(self, name="aa", label=str(self.windupPercent), size=(60, -1), style=wx.ALIGN_CENTER)
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
        self.text_num3 = wx.StaticText(self, name="aa", label=str(self.windupModifier), size=(60, -1), style=wx.ALIGN_CENTER)
        self.text3.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text_num3.SetFont(wx.Font(20, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.text3.SetForegroundColour('#000000')
        self.text_num3.SetForegroundColour('#FF0000')
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
        self.thread_listener_attack_speed = threading.Thread(target=self.listener_attack_speed)
        self.thread_listener_attack_speed.daemon = True
        self.thread_action.daemon = True
        self.thread_key.daemon = True
        self.thread_listener_attack_speed.start()
        self.thread_action.start()
        self.thread_key.start()

    def on_key_down(self, event):
        if event.Key == self.currentKey:
            self.pressTheTriggerButton = True
            if self.onlyLoL and not self.is_pause:
                sendkey(0x2e, 1)
            return self.is_pause
        elif event.Key == "Right":
            self.update_number(self.text_num2, True, 0, 1, 0.01)
            self.Iconize(False)
            return self.is_pause
        elif event.Key == "Left":
            self.update_number(self.text_num2, False, 0, 1, 0.01)
            self.Iconize(False)
            return self.is_pause
        elif event.Key == "Prior":
            self.is_pause = False
            self.SetTransparent(255)
            self.message_text.Label = "已啟動，按住[" + self.currentKey + "]走A"
            self.Iconize(False)
            return False
        elif event.Key == "Next":
            self.is_pause = True
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
            self.pressTheTriggerButton = False
            if self.onlyLoL:
                sendkey(0x2e, 0)
                sendkey(0x2e, 1)
                sendkey(0x2e, 0)
            return self.is_pause
        return True

    def action(self):
        while True:
            if self.pressTheTriggerButton and not self.is_pause:
                self.click(0x2c, self.windupTime)
                self.click(0x2d, self.timeBetweenAttacks)
            else:
                time.sleep(0.01)

    def click(self, key, click_time):
        while click_time > self.minTime and self.pressTheTriggerButton:
            process_time = time.time()
            sendkey(key, 1)
            sendkey(key, 0)
            time.sleep(self.minTime)
            click_time = click_time - (time.time() - process_time)
        if self.pressTheTriggerButton and click_time >= 0:
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
            if self.attackSpeed == speed:
                continue
            self.attackSpeed = speed
            self.attackTime = 1.0 / self.attackSpeed
            self.windupTime = self.attackTime * self.windupPercent
            self.timeBetweenAttacks = self.attackTime - self.windupTime + self.windupModifier

    def on_close(self, event):
        self.Destroy()

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
                self.is_pause = False
                self.SetTransparent(255)
                self.message_text.Label = "已啟動，按住[" + self.currentKey + "]走A"
            elif name == "stop":
                self.is_pause = True
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
            self.windupPercent = num
        elif who == self.text_num3:
            self.windupModifier = num
        self.attackTime = 1.0 / self.attackSpeed
        self.windupTime = self.attackTime * self.windupPercent
        self.timeBetweenAttacks = self.attackTime - self.windupTime + self.windupModifier
        num = str(num)
        if len(num) > 3:
            num = num[0:4]
        who.SetLabel(num)

if __name__ == "__main__":
    app = wx.App(False)
    ui = MainWindow(None, "刀！")
    ui.Centre()
    app.MainLoop()