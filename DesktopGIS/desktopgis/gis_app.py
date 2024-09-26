import sys

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsItem,
)
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QWheelEvent, QPainter, QPen, QColor, QPolygonF
from typing import List


class GISApp(QMainWindow):
    def __init__(self: "GISApp") -> None:
        super().__init__()
        self.file_path = ""  # Путь к открытому
        self.initUI()

    def initUI(self: "GISApp") -> None:
        """Инициализация интерфейса"""

        self.setWindowTitle("Настольная ГИС")
        self.setGeometry(100, 100, 800, 600)

        # Главный виджет
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        # Поле для ввода пути к файлу
        self.filePathEdit = QLineEdit(self)
        self.filePathEdit.setPlaceholderText(
            "Введите путь к файлу или выберите через Обзор..."
        )

        # Кнопка "Обзор"
        self.btnBrowse = QPushButton("Обзор", self)
        self.btnBrowse.clicked.connect(self.openFileDialog)

        # Строка состояния
        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)

        # Виджет для отображения карты
        self.mapView = MapView(self)  # Кастомный QGraphicsView
        self.scene = QGraphicsScene(self.mapView)
        self.mapView.setScene(self.scene)

        # Компоновка элементов
        layout = QVBoxLayout(main_widget)
        layout.addWidget(self.filePathEdit)
        layout.addWidget(self.btnBrowse)
        layout.addWidget(self.mapView)  # Добавляем карту в интерфейс

        # Отображаем окно
        self.show()

        # Рисуем сетку
        self.drawGrid()

    def openFileDialog(self: "GISApp") -> None:
        """Выбор файла"""

        # Открытие выбора файла
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл", "", "Text files (*.txt)"
        )
        if file_name:
            self.file_path = file_name
            self.filePathEdit.setText(file_name)
            self.loadFile(file_name)

    def loadFile(self: "GISApp", file_path: str) -> None:
        """Загрузка данных из файла

        Args:
            file_path (str): Путь к файлу для загрузки данных.
        """

        messages = []  # Список для сообщений

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if not lines:
                self.statusBar.showMessage("Файл пуст.", 5000)
                return

            # Чистим карту перед загрузкой новых данных
            self.scene.clear()
            self.drawGrid()  # Рисуем сетку перед отрисовкой данных

            # Парсим данные из файла
            partial_success = self.parseData(lines, messages)

            # Итоговое сообщение
            if partial_success:
                self.statusBar.showMessage(
                    "Документ прочитан с предупреждениями:\n" + "\n".join(messages),
                    5000,
                )
            else:
                self.statusBar.showMessage("Документ прочитан без ошибок.", 5000)

        except Exception as e:
            self.statusBar.showMessage(f"Ошибка при чтении файла: {e}", 5000)

    def parseData(self: "GISApp", lines: List[str], messages: List[str]) -> bool:
        """Парсинг данных из файла

        Args:
            lines (List[str]): Список строк, считанных из файла.
            messages (List[str]): Список сообщений об ошибках.

        Returns:
            bool: Возвращает True, если нет ошибок, иначе False.
        """

        all_data_valid = True  # Флаг для проверки корректности данных
        for line in lines:
            coords = line.split()
            try:
                coords = list(map(float, coords))
            except ValueError:
                messages.append(f"Некорректные координаты в строке: {line.strip()}")
                all_data_valid = False
                continue

            # Определяем тип фигуры
            if len(coords) == 2:
                self.drawPoint(coords)
            elif len(coords) == 4:
                self.drawLine(coords)
            elif len(coords) >= 6:
                self.drawPolygon(coords)
            else:
                messages.append(f"Ошибка: некорректная строка данных: {line.strip()}")
                all_data_valid = False

        return not all_data_valid  # Возвращаем True, если нет ошибок

    def drawPoint(self: "GISApp", coords: List[float]) -> None:
        """Отрисовка точки

        Args:
            coords (List[float]): Координаты точки в формате [x, y].
        """

        x, y = coords
        point = QGraphicsEllipseItem(x - 5, y - 5, 10, 10)  # Увеличил размер точки
        point.setPen(QPen(Qt.red))  # Красный контур для точки
        point.setBrush(QColor(Qt.black))  # Черная заливка
        self._configureSelectableItem(point)  # Настройка объекта
        self.scene.addItem(point)

    def drawLine(self: "GISApp", coords: List[float]) -> None:
        """Отрисовка линии

        Args:
            coords (List[float]): Координаты линии в формате [x1, y1, x2, y2].
        """

        x1, y1, x2, y2 = coords
        line = QGraphicsLineItem(x1, y1, x2, y2)  # Рисуем линию
        line.setPen(QPen(Qt.blue, 2))  # Устанавливаем синий цвет и толщину линии
        self._configureSelectableItem(line)  # Настройка объекта
        self.scene.addItem(line)

    def drawPolygon(self: "GISApp", coords: List[float]) -> None:
        """Отрисовка полигона

        Args:
            coords (List[float]): Координаты вершин полигона в формате [x1, y1, x2, y2, ...].
        """

        points = []
        for i in range(0, len(coords), 2):
            points.append(QPointF(coords[i], coords[i + 1]))

        polygon = QGraphicsPolygonItem(QPolygonF(points))  # Создаем полигон
        polygon.setPen(
            QPen(Qt.green, 2)
        )  # Устанавливаем зеленый цвет и толщину контура
        polygon.setBrush(QColor(0, 255, 0, 100))  # Полупрозрачная заливка
        self._configureSelectableItem(polygon)  # Настройка объекта
        self.scene.addItem(polygon)

    def _configureSelectableItem(self: "GISApp", item) -> None:
        """Настройка объекта для выбора и обработки событий наведения.

        Args:
            item: Объект, который нужно настроить.
        """

        item.setFlag(QGraphicsItem.ItemIsSelectable, True)  # Делаем объект выбираемым
        item.setAcceptHoverEvents(True)  # Активируем события наведения

    def drawGrid(self: "GISApp") -> None:
        """Рисуем сетку, но не добавляем её"""

        grid_size = 20  # Размер ячейки в пикселях
        width = 800  # Ширина области рисования
        height = 600  # Высота области рисования

        # Отрисовывка вертикальных линий
        for x in range(0, width, grid_size):
            # Используем временные объекты, которые не добавляются в сцену
            line = QGraphicsLineItem(x, 0, x, height)
            line.setPen(QPen(Qt.lightGray))  # Светло-серая линия
            line.setZValue(-1)  # Устанавливаем ниже других объектов
            self.scene.addItem(line)

        # Отрисовываем горизонтальные линии
        for y in range(0, height, grid_size):
            line = QGraphicsLineItem(0, y, width, y)
            line.setPen(QPen(Qt.lightGray))  # Светло-серая линия
            line.setZValue(-1)  # Устанавливаем ниже других объектов
            self.scene.addItem(line)

    def saveFile(self: "GISApp") -> None:
        """Сохраняем изменения в исходный файл"""

        if not self.file_path:
            self.statusBar.showMessage("Нет файла для сохранения", 5000)
            return

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:

                for item in self.scene.items():
                    if isinstance(item, QGraphicsEllipseItem):
                        # Сохраняем точки
                        x = (
                            item.rect().x() + item.rect().width() / 2
                        )  # Получаем координаты центра
                        y = item.rect().y() + item.rect().height() / 2
                        f.write(f"{int(x)} {int(y)}\n")
                    elif (
                        isinstance(item, QGraphicsLineItem)
                        and item.pen().color() != Qt.lightGray
                    ):
                        # Сохраняем линии, исключая линии сетки
                        line = item.line()
                        x1, y1, x2, y2 = line.x1(), line.y1(), line.x2(), line.y2()
                        f.write(f"{int(x1)} {int(y1)} {int(x2)} {int(y2)}\n")
                        objects_saved = True  # Объект сохранён
                    elif isinstance(item, QGraphicsPolygonItem):
                        # Сохраняем полигоны
                        points = item.polygon()
                        point_list = " ".join(
                            f"{int(point.x())} {int(point.y())}" for point in points
                        )
                        f.write(point_list + "\n")

            self.statusBar.showMessage("Изменения сохранены.", 5000)

        except Exception as e:
            self.statusBar.showMessage(f"Ошибка при сохранении: {e}", 5000)

    def keyPressEvent(self: "GISApp", event) -> None:
        """Обработка нажатий клавиш

        Args:
            event: Событие нажатия клавиши.
        """

        if event.key() == Qt.Key_Delete:
            # Удаление выделенных объектов
            selected_items = self.scene.selectedItems()
            if selected_items:
                for item in selected_items:
                    self.scene.removeItem(item)

        if event.key() == Qt.Key_S and event.modifiers() == Qt.ControlModifier:
            # Сохранение файла при нажатии Ctrl + S
            self.saveFile()


class MapView(QGraphicsView):
    def __init__(self: "MapView", parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setDragMode(QGraphicsView.ScrollHandDrag)  # Включаем режим перемещения
        self.setRenderHint(
            QPainter.Antialiasing
        )  # Включаем сглаживание элементов на карте

    def wheelEvent(self: "MapView", event: QWheelEvent) -> None:
        """Обработка масштабирования колесом мыши

        Args:
            event (QWheelEvent): Событие колеса мыши.
        """

        # Обработка масштабирования колесом мыши
        zoom_in_factor = 1.25
        zoom_out_factor = 0.8

        if event.angleDelta().y() > 0:
            # Увеличиваем масштаб
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            # Уменьшаем масштаб
            self.scale(zoom_out_factor, zoom_out_factor)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = GISApp()
    sys.exit(app.exec_())
