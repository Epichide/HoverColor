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
    192:Qt.Key_QuoteLeft
}
print(pyn2Qt_map)
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
            print(f'Alphanumeric key pressed: {key}',GLOBAL_PRESS)
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
        print(f'Key released: {key}',GLOBAL_PRESS)


# Collect events until released
listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
# listener.start()
# listener.join()