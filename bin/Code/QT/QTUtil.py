import gc

from PySide6 import QtCore, QtGui, QtWidgets

import Code


class GarbageCollector(QtCore.QObject):
    """
    http://pydev.blogspot.com.br/2014/03/should-python-garbage-collector-be.html
    Erik Janssens
    Disable automatic garbage collection and instead collect manually
    every INTERVAL milliseconds.

    This is done to ensure that garbage collection only happens in the GUI
    thread, as otherwise Qt can crash.
    """

    INTERVAL = 10000

    def __init__(self):
        QtCore.QObject.__init__(self, None)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.verify)

        self.threshold = gc.get_threshold()
        gc.disable()
        self.timer.start(self.INTERVAL)

    def verify(self):
        # num = gc.collect()
        l0, l1, l2 = gc.get_count()
        num = 0
        if l0 > self.threshold[0]:
            num = gc.collect(0)
            if l1 > self.threshold[1]:
                num = gc.collect(1)
                if l2 > self.threshold[2]:
                    num = gc.collect(2)
        # lista = gc.get_objects()
        # with open("mira", "wb") as f:
        #     for x in lista:
        #         f.write(str(x)+"\n")
        return num

    def collect(self):
        gc.collect()


def beep():
    """
    Pitido del sistema
    """
    QtWidgets.QApplication.beep()


def backgroundGUI():
    """
    Background por defecto del GUI
    """
    return QtWidgets.QApplication.palette().brush(QtGui.QPalette.Active, QtGui.QPalette.Window).color().name()


def backgroundGUIlight(factor):
    """
    Background por defecto del GUI
    """
    return (
        QtWidgets.QApplication.palette()
        .brush(QtGui.QPalette.Active, QtGui.QPalette.Window)
        .color()
        .light(factor)
        .name()
    )


def refresh_gui():
    """
    Procesa eventos pendientes para que se muestren correctamente las windows
    """
    QtCore.QCoreApplication.processEvents()
    QtWidgets.QApplication.processEvents()


def xrefresh_gui():
    """
    Procesa eventos pendientes para que se muestren correctamente las windows
    """
    QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.ExcludeUserInputEvents)


def send_key_widget(widget, key, ckey):
    event_press = QtGui.QKeyEvent(QtGui.QKeyEvent.KeyPress, key, QtCore.Qt.NoModifier, ckey)
    event_release = QtGui.QKeyEvent(QtGui.QKeyEvent.KeyRelease, key, QtCore.Qt.NoModifier, ckey)
    QtCore.QCoreApplication.postEvent(widget, event_press)
    QtCore.QCoreApplication.postEvent(widget, event_release)
    refresh_gui()


dAlineacion = {"i": QtCore.Qt.AlignLeft, "d": QtCore.Qt.AlignRight, "c": QtCore.Qt.AlignCenter}


def qtAlineacion(cAlin):
    """
    Convierte alineacion en letras (i-c-d) en constantes qt
    """
    return dAlineacion.get(cAlin, QtCore.Qt.AlignLeft)


def qtColor(nColor):
    """
    Genera un color a partir de un dato numerico
    """
    return QtGui.QColor(nColor)


def qtColorRGB(r, g, b):
    """
    Genera un color a partir del rgb
    """
    return QtGui.QColor(r, g, b)


def qtBrush(nColor):
    """
    Genera un brush a partir de un dato numerico
    """
    return QtGui.QBrush(qtColor(nColor))


def centraWindow(window):
    """
    Centra la ventana en el escritorio
    """
    screen = QtGui.QGuiApplication.instance().primaryScreen().geometry()
    size = window.geometry()
    window.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)


def escondeWindow(window):
    pos = window.pos()
    screen = QtGui.QGuiApplication.instance().primaryScreen().geometry()
    if Code.is_windows:
        window.move(screen.width() * 10, 0)
    else:
        window.showMinimized()
    return pos


class EscondeWindow:
    def __init__(self, window):
        self.window = window
        self.is_maximized = self.window.isMaximized()

    def __enter__(self):
        if Code.is_windows:
            self.pos = self.window.pos()
            screen = QtGui.QGuiApplication.instance().primaryScreen().geometry()
            self.window.move(screen.width() * 10, 0)
        else:
            self.window.showMinimized()
        return self

    def __exit__(self, type, value, traceback):
        if Code.is_windows:
            self.window.move(self.pos)
        if self.is_maximized:
            self.window.showMaximized()
        else:
            self.window.showNormal()
        refresh_gui()


def colorIcon(xcolor, ancho, alto):
    color = QtGui.QColor(xcolor)
    pm = QtGui.QPixmap(ancho, alto)
    pm.fill(color)
    return QtGui.QIcon(pm)


def tamEscritorio():
    """
    Devuelve ancho,alto del escritorio
    """
    screen = QtGui.QGuiApplication.instance().primaryScreen().availableGeometry()
    return screen.width(), screen.height()


def anchoEscritorio():
    return QtGui.QGuiApplication.instance().primaryScreen().availableGeometry().width()


def altoEscritorio():
    return QtGui.QGuiApplication.instance().primaryScreen().availableGeometry().height()


def salirAplicacion(xid):
    QtWidgets.QApplication.exit(xid)


def ponPortapapeles(dato, tipo="t"):
    cb = QtWidgets.QApplication.clipboard()
    if tipo == "t":
        cb.setText(dato)
    elif tipo == "i":
        cb.setImage(dato)
    elif tipo == "p":
        cb.setPixmap(dato)


def traePortapapeles():
    cb = QtWidgets.QApplication.clipboard()
    return cb.text()


def get_clipboard():
    clipboard = QtWidgets.QApplication.clipboard()
    mimedata = clipboard.mimeData()

    if mimedata.hasImage():
        return "p", mimedata.imageData()
    elif mimedata.hasHtml():
        return "h", mimedata.html()
    elif mimedata.hasHtml():
        return "h", mimedata.html()
    elif mimedata.hasText():
        return "t", mimedata.text()
    return None, None


def shrink(widget):
    r = widget.geometry()
    r.setWidth(0)
    r.setHeight(0)
    widget.setGeometry(r)


def kbdPulsado():
    modifiers = QtWidgets.QApplication.keyboardModifiers()
    is_shift = modifiers == QtCore.Qt.KeyboardModifier.ShiftModifier
    is_control = modifiers == QtCore.Qt.KeyboardModifier.ControlModifier
    is_alt = modifiers == QtCore.Qt.KeyboardModifier.AltModifier
    return is_shift, is_control, is_alt


class EstadoWindow:
    def __init__(self, x):
        self.noEstado = x == QtCore.Qt.WindowNoState
        self.minimizado = x == QtCore.Qt.WindowMinimized
        self.maximizado = x == QtCore.Qt.WindowState.WindowMaximized
        self.fullscreen = x == QtCore.Qt.WindowFullScreen
        self.active = x == QtCore.Qt.WindowActive
