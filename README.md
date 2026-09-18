# CMYK-LAB-HSV Color Converter

Учебное приложение по программированию компьютерной графики.

## Возможности

- интерактивное изменение CMYK, LAB и HSV;
- точный ввод компонентов;
- изменение компонентов ползунками;
- выбор цвета стандартной палитрой Qt;
- автоматический пересчёт всех трёх моделей;
- отображение RGB и HEX;
- предупреждение при выходе LAB → RGB за границы sRGB;
- все математические преобразования реализованы в Python.

Qt используется только для интерфейса.

## Установка

Python 3.10+:

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

## Сборка EXE

```text
pip install pyinstaller
pyinstaller --noconsole --onefile --name ColorModels run.py
```

Готовый файл появится в каталоге `dist`.

## Преобразования

CMYK ↔ RGB ↔ HSV.

CMYK ↔ RGB ↔ XYZ ↔ LAB.

LAB → XYZ → RGB сопровождается проверкой выхода линейных RGB-компонентов за допустимый диапазон sRGB.

## Ограничение

CMYK реализован как математическая модель без ICC-профиля печатного устройства.
LAB использует белую точку D65.
