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
