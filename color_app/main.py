import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QDoubleValidator
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSlider, QVBoxLayout, QWidget, QColorDialog,
    QMessageBox
)
from PySide6.QtWidgets import QMessageBox
from .color_models import cmyk_to_lab, cmyk_to_hsv, lab_to_cmyk, lab_to_hsv, hsv_to_cmyk, hsv_to_lab, cmyk_to_rgb, xyz_to_rgb, lab_to_xyz

class Component(QWidget):
    def __init__(self, name, minimum, maximum, decimals, callback):
        super().__init__()
        self.callback = callback
        self.decimals = decimals
        self.minimum = minimum
        self.maximum = maximum

        self.label = QLabel(name)
        self.edit = QLineEdit()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 10000)

        self.edit.setValidator(QDoubleValidator(minimum, maximum, decimals, self))
        self.slider.valueChanged.connect(self.slider_changed)
        self.edit.editingFinished.connect(self.edit_changed)

        layout = QGridLayout(self)
        layout.addWidget(self.label, 0, 0)
        layout.addWidget(self.edit, 0, 1)
        layout.addWidget(self.slider, 1, 0, 1, 2)

    def set_value(self, value, emit=False):
        value = max(self.minimum, min(self.maximum, value))
        self.edit.blockSignals(True)
        self.slider.blockSignals(True)
        self.edit.setText(f"{value:.{self.decimals}f}")
        pos = round((value - self.minimum) / (self.maximum - self.minimum) * 10000)
        self.slider.setValue(pos)
        self.edit.blockSignals(False)
        self.slider.blockSignals(False)
        if emit:
            self.callback(value)

    def slider_changed(self, pos):
        value = self.minimum + (self.maximum - self.minimum) * pos / 10000
        self.edit.blockSignals(True)
        self.edit.setText(f"{value:.{self.decimals}f}")
        self.edit.blockSignals(False)
        self.callback(value)

    def edit_changed(self):
        try:
            value = float(self.edit.text().replace(",", "."))
        except ValueError:
            return
        self.set_value(value, True)

class ModelBox(QFrame):
    def __init__(self, title, specs, callback):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.callback = callback
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>{title}</b>"))
        self.components = []
        for name, mn, mx, dec in specs:
            component = Component(name, mn, mx, dec, callback)
            self.components.append(component)
            layout.addWidget(component)

    def values(self):
        return [float(c.edit.text().replace(",", ".")) for c in self.components]

    def set_values(self, values):
        for component, value in zip(self.components, values):
            component.set_value(value)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CMYK — LAB — HSV")
        self.resize(1050, 720)
        self.updating = False

        self.cmyk = ModelBox("CMYK", [
            ("C", 0, 100, 2), ("M", 0, 100, 2),
            ("Y", 0, 100, 2), ("K", 0, 100, 2)
        ], lambda _: self.changed("CMYK"))

        self.lab = ModelBox("LAB", [
            ("L*", 0, 100, 2), ("a*", -128, 127, 2),
            ("b*", -128, 127, 2)
        ], lambda _: self.changed("LAB"))

        self.hsv = ModelBox("HSV", [
            ("H", 0, 360, 2), ("S", 0, 100, 2), ("V", 0, 100, 2)
        ], lambda _: self.changed("HSV"))

        self.preview = QFrame()
        self.preview.setMinimumHeight(130)

        self.warning = QLabel()
        self.warning.setStyleSheet("color: #a05a00;")
        self.warning.setWordWrap(True)

        self.palette_button = QPushButton("Выбрать цвет из палитры")
        self.palette_button.clicked.connect(self.choose_color)

        self.help_button = QPushButton("Help")
        self.help_button.clicked.connect(self.show_help)

        self.hex_label = QLabel()   

        models = QHBoxLayout()
        models.addWidget(self.cmyk)
        models.addWidget(self.lab)
        models.addWidget(self.hsv)

        controls = QHBoxLayout()
        controls.addWidget(self.palette_button)
        controls.addWidget(self.help_button)
        controls.addWidget(self.hex_label)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(models)
        layout.addWidget(QLabel("Текущий цвет"))
        layout.addWidget(self.preview)
        layout.addLayout(controls)
        layout.addWidget(self.warning)
        self.setCentralWidget(central)

        self.set_cmyk((0, 100, 100, 0))

    def changed(self, source):
        if self.updating:
            return
        self.updating = True
        warning = False

        if source == "CMYK":
            c, m, y, k = [v / 100 for v in self.cmyk.values()]
            lab = cmyk_to_lab(c, m, y, k)
            hsv = cmyk_to_hsv(c, m, y, k)
            self.lab.set_values(lab)
            self.hsv.set_values((hsv[0], hsv[1] * 100, hsv[2] * 100))
        elif source == "LAB":
            l, a, b = self.lab.values()
            cmyk = lab_to_cmyk(l, a, b)
            hsv = lab_to_hsv(l, a, b)
            self.cmyk.set_values([v * 100 for v in cmyk[:4]])
            self.hsv.set_values((hsv[0], hsv[1] * 100, hsv[2] * 100))
            warning = cmyk[4]
        else:
            h, s, v = self.hsv.values()
            cmyk = hsv_to_cmyk(h, s / 100, v / 100)
            lab = hsv_to_lab(h, s / 100, v / 100)
            self.cmyk.set_values([x * 100 for x in cmyk])
            self.lab.set_values(lab)

        self.update_preview()
        self.warning.setText(
            "Цвет вне диапазона sRGB: при переводе LAB → RGB были выполнены ограничение и округление компонентов."
            if warning else ""
        )
        self.updating = False


    def show_help(self):
        QMessageBox.information(
        self,
        "Help",
        "Как пользоваться приложением\n\n"
        "1. Выбор цвета\n"
        "Нажмите «Выбрать цвет из палитры», чтобы выбрать исходный цвет "
        "с помощью стандартного диалога Qt.\n\n"
        "2. Точный ввод\n"
        "В каждой цветовой модели можно вручную ввести значение "
        "компоненты в соответствующее поле.\n\n"
        "3. Ползунки\n"
        "Передвигайте ползунок, чтобы плавно изменять значение компоненты.\n\n"
        "4. Автоматический пересчёт\n"
        "При изменении любой компоненты CMYK, LAB или HSV приложение "
        "автоматически пересчитывает остальные две цветовые модели. "
        "Их поля и ползунки также обновляются.\n\n"
        "5. Диапазоны\n"
        "CMYK: C, M, Y, K — 0–100%.\n"
        "LAB: L* — 0–100, a* и b* — -128–127.\n"
        "HSV: H — 0–360°, S и V — 0–100%.\n\n"
        "6. Предупреждение\n"
        "Некоторые цвета LAB невозможно точно представить в пространстве "
        "sRGB. В таком случае приложение ограничивает значения RGB "
        "допустимым диапазоном и показывает предупреждение."
        )
    

    def set_cmyk(self, values):
        self.cmyk.set_values([v * 100 for v in values])
        self.changed("CMYK")

    def choose_color(self):
        color = QColorDialog.getColor(QColor(self.rgb_qcolor()), self, "Выбор цвета")
        if not color.isValid():
            return
        self.updating = True
        self.set_cmyk((
            color.cyanF(), color.magentaF(), color.yellowF(), color.blackF()
        ))
        self.updating = False
        self.changed("CMYK")

    def rgb_qcolor(self):
        c, m, y, k = [v / 100 for v in self.cmyk.values()]
        r, g, b = cmyk_to_rgb(c, m, y, k)
        return QColor(round(r), round(g), round(b))

    def update_preview(self):
        color = self.rgb_qcolor()
        self.preview.setStyleSheet(
            f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});"
        )
        self.hex_label.setText(f"RGB: {color.red()}, {color.green()}, {color.blue()}    HEX: {color.name()}")

def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()
