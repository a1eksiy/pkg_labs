import numpy as np
from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,QSpinBox,QSlider,QFileDialog,QMessageBox,QGroupBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QPixmap
from processing import filters
from processing.histogram import histogram_data

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Лабораторная работа 3 — Вариант 5")
        self.resize(1100,750)
        self.original=None
        self.current=None
        central=QWidget(); self.setCentralWidget(central)
        layout=QVBoxLayout(central)
        toolbar=QHBoxLayout()
        self.open_btn=QPushButton("Открыть изображение")
        self.save_btn=QPushButton("Сохранить результат")
        self.reset_btn=QPushButton("Сброс")
        toolbar.addWidget(self.open_btn); toolbar.addWidget(self.save_btn); toolbar.addWidget(self.reset_btn)
        layout.addLayout(toolbar)
        controls=QHBoxLayout()
        self.method=QComboBox()
        self.method.addItems(["Медианный фильтр","Минимум (rank)","Максимум (rank)","Процентильный фильтр","Линейное контрастирование","Эквализация RGB","Эквализация яркости HSV"])
        self.radius=QSpinBox(); self.radius.setRange(1,10); self.radius.setValue(1)
        self.percent=QSlider(Qt.Horizontal); self.percent.setRange(0,100); self.percent.setValue(50)
        self.apply_btn=QPushButton("Применить")
        controls.addWidget(QLabel("Метод:")); controls.addWidget(self.method); controls.addWidget(QLabel("Радиус:")); controls.addWidget(self.radius)
        controls.addWidget(QLabel("Процентиль:")); controls.addWidget(self.percent); controls.addWidget(self.apply_btn)
        layout.addLayout(controls)
        images=QHBoxLayout()
        self.left=QLabel("Исходное изображение"); self.right=QLabel("Результат")
        for label in (self.left,self.right):
            label.setAlignment(Qt.AlignCenter); label.setMinimumSize(450,400); label.setStyleSheet("border:1px solid gray")
        images.addWidget(self.left); images.addWidget(self.right); layout.addLayout(images,1)
        self.hist=QLabel("Гистограммы: загрузите изображение")
        self.hist.setWordWrap(True); layout.addWidget(self.hist)
        self.open_btn.clicked.connect(self.open_image); self.save_btn.clicked.connect(self.save_image)
        self.reset_btn.clicked.connect(self.reset); self.apply_btn.clicked.connect(self.apply)
        self.percent.valueChanged.connect(lambda v: self.percent.setToolTip(f"Процентиль: {v}"))
    def open_image(self):
        path,_=QFileDialog.getOpenFileName(self,"Открыть изображение","","Изображения (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)")
        if not path: return
        q=QImage(path)
        if q.isNull():
            QMessageBox.warning(self,"Ошибка","Не удалось загрузить изображение."); return
        q=q.convertToFormat(QImage.Format_RGB888)
        w,h=q.width(),q.height()
        ptr=q.bits()
        arr=np.frombuffer(ptr,dtype=np.uint8).reshape(h,w,3).copy()
        self.original=arr; self.current=arr.copy()
        self.show_image(self.left,arr); self.show_image(self.right,arr); self.update_hist()
    def show_image(self,label,array):
        h,w,_=array.shape
        q=QImage(array.data,w,h,3*w,QImage.Format_RGB888).copy()
        label.setPixmap(QPixmap.fromImage(q).scaled(label.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.original is not None:
            self.show_image(self.left,self.original); self.show_image(self.right,self.current)
    def apply(self):
        if self.original is None: return
        name=self.method.currentText(); r=self.radius.value()
        if name=="Медианный фильтр": out=filters.median_filter(self.original,r)
        elif name=="Минимум (rank)": out=filters.minimum_filter(self.original,r)
        elif name=="Максимум (rank)": out=filters.maximum_filter(self.original,r)
        elif name=="Процентильный фильтр": out=filters.rank_filter(self.original,r,self.percent.value())
        elif name=="Линейное контрастирование": out=filters.linear_contrast(self.original)
        elif name=="Эквализация RGB": out=filters.histogram_equalization_rgb(self.original)
        else: out=filters.histogram_equalization_value(self.original)
        self.current=out; self.show_image(self.right,out); self.update_hist()
    def reset(self):
        if self.original is None: return
        self.current=self.original.copy(); self.show_image(self.right,self.current); self.update_hist()
    def save_image(self):
        if self.current is None: return
        path,_=QFileDialog.getSaveFileName(self,"Сохранить изображение","","PNG (*.png);;JPEG (*.jpg)")
        if path:
            h,w,_=self.current.shape
            q=QImage(self.current.data,w,h,3*w,QImage.Format_RGB888).copy()
            if not q.save(path): QMessageBox.warning(self,"Ошибка","Не удалось сохранить файл.")
    def update_hist(self):
        if self.current is None: return
        hist=histogram_data(self.current)
        summaries=[]
        for name,h in zip(("R","G","B"),hist):
            summaries.append(f"{name}: min={np.where(h>0)[0][0]}, max={np.where(h>0)[0][-1]}, среднее={np.average(np.arange(256),weights=h):.1f}")
        self.hist.setText("Гистограммы результата (статистика каналов): "+ " | ".join(summaries))
