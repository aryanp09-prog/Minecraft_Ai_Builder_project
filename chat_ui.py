# =============================================================
#  chat_ui.py  —  Minimizes game window then shows InputBox
# =============================================================

import threading
import subprocess
import tempfile
import os
import ctypes
import time

from direct.gui.DirectGui import DirectButton, DirectLabel
from panda3d.core import TransparencyAttrib

SW_MINIMIZE = 6
SW_RESTORE  = 9


def _get_panda_hwnd():
    """Find the Panda3D window handle."""
    hwnd = ctypes.windll.user32.FindWindowW(None, "Panda")
    return hwnd


def _vbs_input(history):
    """Opens a native Windows InputBox via PowerShell."""
    safe = history.replace('"', "'").replace('\n', ' | ')
    cmd = (
        'Add-Type -AssemblyName Microsoft.VisualBasic; '
        f'[Microsoft.VisualBasic.Interaction]::InputBox("{safe}", "AI Builder", "")'
    )
    try:
        proc = subprocess.run(
            ['powershell', '-NoProfile', '-Command', cmd],
            capture_output=True, text=True, timeout=120
        )
        text = proc.stdout.strip()
        return text if text else None
    except Exception as e:
        print("Dialog error:", e)
        return None


class ChatUI:

    def __init__(self, game, onSubmit):
        self.game     = game
        self.onSubmit = onSubmit
        self.isOpen   = False
        self.messages = []
        self._buildUI()

    def _buildUI(self):
        self.btn = DirectButton(
            text       = '[ Click Here to Talk to AI Builder ]',
            text_fg    = (0.2, 1, 0.2, 1),
            text_scale = 0.07,
            frameColor = (0, 0, 0, 0.7),
            frameSize  = (-3.5, 3.5, -0.15, 0.22),
            pos        = (0, 0, -0.12),
            parent     = base.a2dTopCenter,
            command    = self.open,
            relief     = 'flat',
        )
        self.btn.setTransparency(TransparencyAttrib.MAlpha)

        self.statusLabel = DirectLabel(
            text       = 'Press Escape then click the button above to build',
            text_fg    = (0.8, 0.8, 0.8, 1),
            text_scale = 0.05,
            frameColor = (0, 0, 0, 0.5),
            frameSize  = (-5, 5, -0.12, 0.15),
            pos        = (0, 0, -0.28),
            parent     = base.a2dTopCenter,
        )
        self.statusLabel.setTransparency(TransparencyAttrib.MAlpha)

    def open(self):
        if self.isOpen:
            return
        self.isOpen = True
        self.game.releaseMouse()
        self.statusLabel['text'] = 'Type your prompt in the popup window...'
        t = threading.Thread(target=self._showDialog, daemon=True)
        t.start()

    def _showDialog(self):
        # minimize Panda3D window so dialog appears on top
        hwnd = _get_panda_hwnd()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
            time.sleep(0.3)

        if self.messages:
            history = ' | '.join(self.messages[-3:]) + ' | Enter prompt:'
        else:
            history = 'Build: house / tower / pyramid / wall | Size: tiny small big huge | Material: grass dirt sand stone | Example: build a big stone house'

        result = _vbs_input(history)

        # restore Panda3D window
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
            time.sleep(0.2)

        if result and result.strip():
            taskMgr.doMethodLater(0.1, lambda t: self._deliver(result.strip(), t), 'chat-deliver')
        else:
            taskMgr.doMethodLater(0.1, lambda t: self._cancel(t), 'chat-cancel')

    def _deliver(self, text, task):
        self.isOpen = False
        self.messages.append('You: ' + text)
        self.statusLabel['text'] = 'You: ' + text
        self.game.captureMouse()
        self.onSubmit(text)
        return task.done

    def _cancel(self, task):
        self.isOpen = False
        self.statusLabel['text'] = 'Cancelled. Press Escape then click button to try again.'
        self.game.captureMouse()
        return task.done

    def companionSay(self, text):
        self.messages.append('AI: ' + text)
        self.statusLabel['text'] = 'AI: ' + text
        print('AI:', text)

    def error(self, text):
        self.messages.append('[!] ' + text)
        self.statusLabel['text'] = '[!] ' + text
        print('[!]', text)
