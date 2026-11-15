import sys

def _enable_dpi_awareness():
    """
    Must be done BEFORE the first window; otherwise Windows enlarges the
    whole rendering itself and CTk enlarges it again on top: blurry text and
    a window that overflows the screen. CustomTkinter tries this setting on
    its own but does not always manage; here we make sure of it.
    """
    if sys.platform != "win32":
        return
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)      # per monitor
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()       # older Windows
        except Exception:
            pass


def _work_area(root):
    """Usable screen area, taskbar excluded, in real pixels."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        try:
            rect = wintypes.RECT()
            if ctypes.windll.user32.SystemParametersInfoW(
                    0x0030, 0, ctypes.byref(rect), 0):       # SPI_GETWORKAREA
                return rect.right - rect.left, rect.bottom - rect.top
        except Exception:
            pass
    return root.winfo_screenwidth(), root.winfo_screenheight() - 80


# ---------------------------------------------------------------------
#  A RESPONSIVE WINDOW WHILE A WORKER THREAD COMPUTES
# ---------------------------------------------------------------------
# The draw and the simulation run on a thread, in pure Python, so the
# worker holds the GIL. Tkinter releases the GIL around every call into
# Tcl and must take it back afterwards; by default Python only asks a
# running thread to hand it over every 5 ms (sys.getswitchinterval()).
# A screen update made of a few hundred Tk calls could therefore wait
# hundreds of milliseconds: measured, one progress-bar update during a
# Monte Carlo took 0.36 s. While a job runs, the interval is lowered to
# 0.5 ms; the worker loses a few percent of speed, the window stays
# fluid. A counter allows two jobs to overlap safely.

import threading as _threading

FAST_SWITCH = 0.0005
_switch_lock = _threading.Lock()
_switch_users = 0
_switch_saved = None


def begin_background_work():
    global _switch_users, _switch_saved
    with _switch_lock:
        if _switch_users == 0:
            _switch_saved = sys.getswitchinterval()
            sys.setswitchinterval(FAST_SWITCH)
        _switch_users += 1


def end_background_work():
    global _switch_users
    with _switch_lock:
        if _switch_users == 0:
            return
        _switch_users -= 1
        if _switch_users == 0 and _switch_saved is not None:
            sys.setswitchinterval(_switch_saved)
