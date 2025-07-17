from pynput import keyboard
from pynput.keyboard import Key, Controller
from PyQt5.QtCore import QEventLoop, Qt
GLOBAL_PRESS=[]
pyn2Qt_map={
    Key.alt.value.vk:   Qt.Key_Alt,
    Key.alt_l.value.vk: Qt.Key_Alt,
    Key.alt_r.value.vk: Qt.Key_Alt,
    Key.ctrl.value.vk:  Qt.Key_Control,
    Key.ctrl_l.value.vk: Qt.Key_Control,
    Key.ctrl_r.value.vk: Qt.Key_Control,
    Key.shift.value.vk:  Qt.Key_Shift,
    Key.shift_l.value.vk: Qt.Key_Shift,
    Key.shift_r.value.vk: Qt.Key_Shift,
    Key.caps_lock : Qt.Key_CapsLock,
    ord('`'):Qt.Key_QuoteLeft,
    ord('~'): Qt.Key_QuoteLeft,
    0x25: Qt.Key_Left,
    0x26: Qt.Key_Up,
    0x27: Qt.Key_Right,
    0x28: Qt.Key_Down,
    0x08: Qt.Key_Backspace,
    0x09: Qt.Key_Tab,
    0x0C: Qt.Key_Clear,
    0x0D: Qt.Key_Return,  # 同时映射 Qt.Key_Enter
    0x10: Qt.Key_Shift,
    0x11: Qt.Key_Control,
    0x12: Qt.Key_Alt,
    0x13: Qt.Key_Pause,
    0x14: Qt.Key_CapsLock,
    0x1B: Qt.Key_Escape,
    0x20: Qt.Key_Space,
    0x21: Qt.Key_PageUp,
    0x22: Qt.Key_PageDown,
    0x23: Qt.Key_End,
    0x24: Qt.Key_Home,
    0x29: Qt.Key_Select,
    0x2A: Qt.Key_Print,
    0x2B: Qt.Key_Execute,
    0x2C: Qt.Key_Printer,
    0x2D: Qt.Key_Insert,
    0x2E: Qt.Key_Delete,
    0x2F: Qt.Key_Help,
    # 小键盘数字键
    0x60: Qt.Key_0,  # 小键盘0
    0x61: Qt.Key_1,  # 小键盘1
    0x62: Qt.Key_2,  # 小键盘2
    0x63: Qt.Key_3,  # 小键盘3
    0x64: Qt.Key_4,  # 小键盘4
    0x65: Qt.Key_5,  # 小键盘5
    0x66: Qt.Key_6,  # 小键盘6
    0x67: Qt.Key_7,  # 小键盘7
    0x68: Qt.Key_8,  # 小键盘8
    0x69: Qt.Key_9,  # 小键盘9

    # 小键盘功能键
    0x6A: Qt.Key_Asterisk,  # 小键盘*
    0x6B: Qt.Key_Plus,  # 小键盘+
    0x6C: Qt.Key_Comma,  # 小键盘,（部分键盘为分隔符）
    0x6D: Qt.Key_Minus,  # 小键盘-
    0x6E: Qt.Key_Period,  # 小键盘.
    0x6F: Qt.Key_Slash,  # 小键盘/
    0x0D: Qt.Key_Enter,  # 小键盘Enter（与主键盘Enter共享虚拟键码）
    0x24: Qt.Key_Return,  # 部分系统中小键盘Enter的映射（视系统而定）
    0x90: Qt.Key_NumLock,  # NumLock键
    0xD7: Qt.Key_Asterisk, #*
    # 补充其他常见键（非小键盘但可能关联）
    0xC0: Qt.Key_QuoteLeft,  # 左上角`/~键
    0x08: Qt.Key_Backspace,  # 退格键
    0x20: Qt.Key_Space,  # 空格键
    0x30: Qt.Key_0,  # 同时映射 Qt.Key_ParenRight
    0x31: Qt.Key_1,  # 同时映射 Qt.Key_Exclam
    0x32: Qt.Key_2,  # 同时映射 Qt.Key_At
    0x33: Qt.Key_3,  # 同时映射 Qt.Key_NumberSign
    0x34: Qt.Key_4,  # 同时映射 Qt.Key_Dollar
    0x35: Qt.Key_5,  # 同时映射 Qt.Key_Percent
    0x36: Qt.Key_6,  # 同时映射 Qt.Key_AsciiCircum
    0x37: Qt.Key_7,  # 同时映射 Qt.Key_Ampersand
    0x38: Qt.Key_8,  # 同时映射 Qt.Key_Asterisk
    0x39: Qt.Key_9,  # 同时映射 Qt.Key_ParenLeft
    0x28: Qt.Key_Equal, # =
    0x41: Qt.Key_A,
    0x42: Qt.Key_B,
    0x43: Qt.Key_C,
    0x44: Qt.Key_D,
    0x45: Qt.Key_E,
    0x46: Qt.Key_F,
    0x47: Qt.Key_G,
    0x48: Qt.Key_H,
    0x49: Qt.Key_I,
    0x4A: Qt.Key_J,
    0x4B: Qt.Key_K,
    0x4C: Qt.Key_L,
    0x4D: Qt.Key_M,
    0x4E: Qt.Key_N,
    0x4F: Qt.Key_O,
    0x50: Qt.Key_P,
    0x51: Qt.Key_Q,
    0x52: Qt.Key_R,
    0x53: Qt.Key_S,
    0x54: Qt.Key_T,
    0x55: Qt.Key_U,
    0x56: Qt.Key_V,
    0x57: Qt.Key_W,
    0x58: Qt.Key_X,
    0x59: Qt.Key_Y,
    0x5A: Qt.Key_Z,
    0x6A: Qt.Key_multiply,
    0x70: Qt.Key_F1,
    0x71: Qt.Key_F2,
    0x72: Qt.Key_F3,
    0x73: Qt.Key_F4,
    0x74: Qt.Key_F5,
    0x75: Qt.Key_F6,
    0x76: Qt.Key_F7,
    0x77: Qt.Key_F8,
    0x78: Qt.Key_F9,
    0x79: Qt.Key_F10,
    0x7A: Qt.Key_F11,
    0x7B: Qt.Key_F12,
    0x7C: Qt.Key_F13,
    0x7D: Qt.Key_F14,
    0x7E: Qt.Key_F15,
    0x7F: Qt.Key_F16,
    0x80: Qt.Key_F17,
    0x81: Qt.Key_F18,
    0x82: Qt.Key_F19,
    0x83: Qt.Key_F20,
    0x84: Qt.Key_F21,
    0x85: Qt.Key_F22,
    0x86: Qt.Key_F23,
    0x87: Qt.Key_F24,
    0x90: Qt.Key_NumLock,
    0x91: Qt.Key_ScrollLock,
    0xAE: Qt.Key_VolumeDown,
    0xAF: Qt.Key_VolumeUp,
    0xAD: Qt.Key_VolumeMute,
    0xB2: Qt.Key_MediaStop,
    0xB3: Qt.Key_MediaPlay,
    0xBB: Qt.Key_Plus,  # 同时映射 Qt.Key_Equal
    0xBD: Qt.Key_Minus,  # 同时映射 Qt.Key_Underscore
    0xBA: Qt.Key_Semicolon,  # 同时映射 Qt.Key_Colon
    0xBC: Qt.Key_Comma,  # 同时映射 Qt.Key_Less
    0xBE: Qt.Key_Period,  # 同时映射 Qt.Key_Greater
    0xBF: Qt.Key_Slash,  # 同时映射 Qt.Key_Question
    0xDB: Qt.Key_BracketLeft,  # 同时映射 Qt.Key_BraceLeft
    0xDD: Qt.Key_BracketRight,  # 同时映射 Qt.Key_BraceRight
    0xDC: Qt.Key_Bar,  # 同时映射 Qt.Key_Backslash
    0xDE: Qt.Key_Apostrophe,  # 同时映射 Qt.Key_QuoteDbl
    0xC0: Qt.Key_QuoteLeft  # 同时映射 Qt.Key_AsciiTilde
}


# print(pyn2Qt_map)
def on_press(key):
    try:
        if hasattr(key,"value"):
            vk=key.value.vk
        else:
            vk=key.vk
        if vk in pyn2Qt_map:
            vk=pyn2Qt_map[vk]
        if vk not in  GLOBAL_PRESS:
            GLOBAL_PRESS.append(vk)
            # print(f'Alphanumeric key pressed: {key}',GLOBAL_PRESS)
    except AttributeError:
        print(f'Special key pressed: {key}')

def on_release(key):
    global GLOBAL_PRESS
    if hasattr(key, "value"):
        vk = key.value.vk
    else:
        vk = key.vk
    if vk in pyn2Qt_map:
        vk = pyn2Qt_map[vk]
    if vk  in GLOBAL_PRESS:
        GLOBAL_PRESS.remove(vk)
        # print(f'Key released: {key}',GLOBAL_PRESS)


# Collect events until released
listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
# listener.start()
# listener.join()