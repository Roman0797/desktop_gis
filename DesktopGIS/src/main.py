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
from functools import wraps
from typing import Callable


def configure_graphics_item(
    pen_color: QColor,
    pen_width: int = 1,
    brush_color: QColor = None,
    selectable: bool = True,
):
    """Декоратор для настройки графических объектов (QGraphicsItem).

    Args:
        pen_color (QColor): Цвет контура.
        pen_width (int, optional): Ширина контура. По умолчанию 1.
        brush_color (QColor, optional): Цвет заливки. Если None, заливка не используется.
        selectable (bool, optional): Возможность выбора объекта. По умолчанию True.
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, coords: list[float]):
            # Создаем графический объект
            item = func(self, coords)
            # Настройка объекта (контур и заливка)
            item.setPen(QPen(pen_color, pen_width))
            if brush_color:
                item.setBrush(brush_color)

            # Настройка для выбора и событий наведения
            if selectable:
                item.setFlag(QGraphicsItem.ItemIsSelectable, True)
            item.setAcceptHoverEvents(True)

            # Добавляем объект
            self.scene.addItem(item)
            return item

        return wrapper

    return decorator


class GISApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.file_path = ""  # Путь к открытому файлу
        self.init_ui()

    def init_ui(self) -> None:
        """Инициализация интерфейса"""
        self.setWindowTitle("Настольная ГИС")
        self.setGeometry(100, 100, 800, 600)

        # Главный виджет
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        # Поле для ввода пути к файлу
        self.filePathEdit = QLineEdit(self)
        self.filePathEdit.returnPressed.connect(self.load_file_from_input)
        self.filePathEdit.setPlaceholderText(
            "Введите путь к файлу или выберите через Обзор..."
        )

        # Кнопка "Обзор"
        self.btnBrowse = QPushButton("Обзор", self)
        self.btnBrowse.clicked.connect(self.open_file_dialog)

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
        layout.addWidget(self.mapView)

        # Отображаем окно
        self.show()

        # Рисуем сетку
        self.draw_grid()

    def open_file_dialog(self) -> None:
        """Открытие диалога для выбора файла"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Открыть файл", "", "Text files (*.txt)"
        )
        if file_name:
            self.file_path = file_name
            self.filePathEdit.setText(file_name)
            self.load_file(file_name)

    def load_file_from_input(self) -> None:
        """Загрузка файла из текстового поля"""
        file_path = self.filePathEdit.text()  # Получаем текст из поля
        if file_path:
            self.file_path = file_path
            self.load_file(file_path)

    def load_file(self, file_path: str) -> None:
        """Загрузка данных из файла"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except (IOError, OSError) as e:
            self._show_status_message(f"Ошибка при открытии файла: {e}")
            return

        if not lines:
            self._show_status_message("Файл пуст.")
            return

        # Очищаем сцену и рисуем сетку
        self.scene.clear()
        self.draw_grid()

        # Парсинг данных
        messages = []
        try:
            partial_success = self.parse_data(lines, messages)
        except ValueError as e:
            self._show_status_message(f"Ошибка при парсинге данных: {e}")
            return

        # Обработка результатов парсинга
        if partial_success:
            self._show_status_message(
                f"Документ прочитан с предупреждениями:\n" + "\n".join(messages)
            )
        else:
            self._show_status_message("Документ прочитан без ошибок.")

    def parse_data(self, lines: list[str], messages: list[str]) -> bool:
        """Парсинг данных из файла

        Args:
            lines (List[str]): Список строк, считанных из файла.
            messages (List[str]): Список сообщений об ошибках.

        Returns:
            bool: Возвращает True, если нет ошибок, иначе False.
        """

        all_data_valid = True
        for line in lines:
            coords = line.split()
            try:
                coords = list(map(float, coords))
            except ValueError:
                messages.append(f"Некорректные координаты в строке: {line.strip()}")
                all_data_valid = False
                continue

            match len(coords):
                case 2:
                    self.draw_point(coords)
                case 4:
                    self.draw_line(coords)
                case n if n >= 6 and n % 2 == 0:
                    self.draw_polygon(coords)
                case _:
                    messages.append(
                        f"Ошибка: некорректная строка данных: {line.strip()}"
                    )
                    all_data_valid = False

        return not all_data_valid

    @configure_graphics_item(Qt.red, 1, QColor(Qt.black))
    def draw_point(self, coords: list[float]) -> QGraphicsEllipseItem:
        """Отрисовка точки.

        Args:
            coords (List[float]): Координаты точки в формате [x, y].
        """
        x, y = coords
        return QGraphicsEllipseItem(x - 5, y - 5, 10, 10)

    @configure_graphics_item(Qt.blue, 2)
    def draw_line(self, coords: list[float]) -> QGraphicsLineItem:
        """Отрисовка линии.

        Args:
            coords (List[float]): Координаты линии в формате [x1, y1, x2, y2].
        """
        x1, y1, x2, y2 = coords
        return QGraphicsLineItem(x1, y1, x2, y2)

    @configure_graphics_item(Qt.green, 2, QColor(0, 255, 0, 100))
    def draw_polygon(self, coords: list[float]) -> QGraphicsPolygonItem:
        """Отрисовка полигона.

        Args:
            coords (List[float]): Координаты вершин полигона в формате [x1, y1, x2, y2, ...].
        """

        points = [QPointF(coords[i], coords[i + 1]) for i in range(0, len(coords), 2)]
        return QGraphicsPolygonItem(QPolygonF(points))

    def draw_grid(self) -> None:
        """Рисуем сетку"""
        grid_size = 20
        width, height = 800, 600
        for x in range(0, width, grid_size):
            self._draw_grid_line(x, 0, x, height)
        for y in range(0, height, grid_size):
            self._draw_grid_line(0, y, width, y)

    def _draw_grid_line(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Вспомогательный метод для рисования линии сетки"""
        line = QGraphicsLineItem(x1, y1, x2, y2)
        line.setPen(QPen(Qt.lightGray))
        line.setZValue(-1)
        self.scene.addItem(line)

    def save_file(self) -> None:
        """Сохраняем изменения в исходный файл"""
        if not self.file_path:
            self.statusBar.showMessage("Нет файла для сохранения", 5000)
            return

        save_data = []

        # Сбор данных для сохранения
        try:
            for item in self.scene.items():
                match item:
                    case QGraphicsEllipseItem():
                        # Сохраняем точки
                        x = (
                            item.rect().x() + item.rect().width() / 2
                        )  # Координаты центра
                        y = item.rect().y() + item.rect().height() / 2
                        save_data.append(f"{int(x)} {int(y)}\n")

                    case QGraphicsLineItem() if item.pen().color() != Qt.lightGray:
                        # Сохраняем линии, исключая линии сетки
                        line = item.line()
                        x1, y1, x2, y2 = line.x1(), line.y1(), line.x2(), line.y2()
                        save_data.append(f"{int(x1)} {int(y1)} {int(x2)} {int(y2)}\n")

                    case QGraphicsPolygonItem():
                        # Сохраняем полигоны
                        points = item.polygon()
                        point_list = " ".join(
                            f"{int(point.x())} {int(point.y())}" for point in points
                        )
                        save_data.append(point_list + "\n")

        except AttributeError as e:
            self.statusBar.showMessage(f"Ошибка данных: {e}", 5000)
            return
        # Запись данных в файл
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.writelines(save_data)
            self.statusBar.showMessage("Изменения сохранены.", 5000)
        except (IOError, OSError) as e:
            self.statusBar.showMessage(f"Ошибка при сохранении файла: {e}", 5000)

    def keyPressEvent(self, event) -> None:
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
            self.save_file()

        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.load_file_from_input()  # Загрузка файла по нажатию Enter

    def _show_status_message(self, message: str, timeout: int = 5000) -> None:
        """Отображение сообщения в статусбаре"""
        self.statusBar.showMessage(message, timeout)


class MapView(QGraphicsView):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setDragMode(QGraphicsView.ScrollHandDrag)  # Включаем режим перемещения
        self.setRenderHint(
            QPainter.Antialiasing
        )  # Включаем сглаживание элементов на карте

    def wheelEvent(self, event: QWheelEvent) -> None:
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
