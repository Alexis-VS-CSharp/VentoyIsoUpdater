"""
Themed replacements for tkinter.messagebox.

tkinter.messagebox always renders with the OS's native Tk look (light
background, native buttons), which clashes with this app's dark
customtkinter theme. These are drop-in equivalents built on CTkToplevel
instead, matching the rest of the UI.
"""

import customtkinter as ctk
from gui.i18n import t

_ICONS = {
    "info":     ("ℹ", "#3498db"),
    "warning":  ("⚠", "#f39c12"),
    "error":    ("✕", "#e74c3c"),
    "question": ("?", "#8e44ad"),
}


class _MessageDialog(ctk.CTkToplevel):
    def __init__(self, parent, title: str, message: str, kind: str, buttons: list):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        try:
            self.transient(parent)
        except Exception:
            pass
        self._result = False

        symbol, color = _ICONS.get(kind, _ICONS["info"])

        self.grid_columnconfigure(0, weight=1)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=0, column=0, sticky="nsew", padx=24, pady=(24, 16))
        body.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            body, text=symbol, font=ctk.CTkFont(size=30, weight="bold"),
            text_color=color, width=44
        ).grid(row=0, column=0, rowspan=2, sticky="n", padx=(0, 16))

        ctk.CTkLabel(
            body, text=title, font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w", justify="left"
        ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            body, text=message, font=ctk.CTkFont(size=12),
            text_color="gray80", anchor="w", justify="left", wraplength=380
        ).grid(row=1, column=1, sticky="w", pady=(8, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=1, column=0, pady=(0, 20))

        for label, value, is_primary in buttons:
            fg = color if is_primary else "#3a3a3a"
            hov = color if is_primary else "#4a4a4a"
            ctk.CTkButton(
                btn_row, text=label, width=100, height=32,
                fg_color=fg, hover_color=hov,
                command=lambda v=value: self._close(v),
            ).pack(side="left", padx=6)

        default_value = buttons[-1][1]
        self.protocol("WM_DELETE_WINDOW", lambda: self._close(False))
        self.bind("<Return>", lambda e: self._close(default_value))
        self.bind("<Escape>", lambda e: self._close(False))

        self.update_idletasks()
        self._center_over(parent)
        self.grab_set()
        self.focus_force()

    def _center_over(self, parent) -> None:
        w = max(self.winfo_reqwidth(), 320)
        h = self.winfo_reqheight()
        try:
            px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
            py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        except Exception:
            px = self.winfo_screenwidth() // 2 - w // 2
            py = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{max(px, 0)}+{max(py, 0)}")

    def _close(self, value) -> None:
        self._result = value
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def wait(self):
        self.wait_window(self)
        return self._result


def _show(parent, title: str, message: str, kind: str) -> None:
    _MessageDialog(parent, title, message, kind, [(t('OK'), True, True)]).wait()


def show_info(parent, title: str, message: str) -> None:
    _show(parent, title, message, "info")


def show_warning(parent, title: str, message: str) -> None:
    _show(parent, title, message, "warning")


def show_error(parent, title: str, message: str) -> None:
    _show(parent, title, message, "error")


def ask_yes_no(parent, title: str, message: str, danger: bool = False) -> bool:
    """Modal Yes/No confirmation. `danger=True` tints it red (destructive action)
    instead of the app's default purple accent."""
    kind = "error" if danger else "question"
    buttons = [(t('Non'), False, False), (t('Oui'), True, True)]
    return _MessageDialog(parent, title, message, kind, buttons).wait()
