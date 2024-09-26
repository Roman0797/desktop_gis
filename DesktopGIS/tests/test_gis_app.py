import pytest

from unittest.mock import patch, mock_open
from desktopgis.gis_app import GISApp


@pytest.fixture
def app(qtbot):
    """Фикстура для создания и отображения GISApp."""
    test_app = GISApp()
    qtbot.addWidget(test_app)  # добавляю виджет к qtbot
    return test_app


@pytest.fixture
def valid_data():
    """Фикстура для предоставления валидных данных для тестов."""
    return "100 100\n200 200 300 300\n100 100 200 100 150 200"


@pytest.fixture
def invalid_data():
    """Фикстура для предоставления невалидных данных для тестов."""
    return "100 100\ninvalid_data\n200 200 300"


def test_initialization(app):
    """Тест начального состояния GISApp."""
    assert app.windowTitle() == "Настольная ГИС"
    assert app.file_path == ""
    assert app.filePathEdit.text() == ""


def test_open_file_dialog(app, qtbot):
    """Тест функциональности диалога открытия файла."""
    with patch(
        "PyQt5.QtWidgets.QFileDialog.getOpenFileName", return_value=("test.txt", "")
    ):
        app.openFileDialog()
        assert app.filePathEdit.text() == "test.txt"


def test_load_file_valid(app, qtbot, valid_data):
    """Тест загрузки валидного файла."""
    with patch("builtins.open", mock_open(read_data=valid_data)):
        app.loadFile("dummy_path.txt")

    # После загрузки должны быть элементы
    assert len(app.scene.items()) > 0


def test_load_file_invalid(app, qtbot, invalid_data):
    """Тест загрузки файла с невалидными данными."""
    with patch("builtins.open", mock_open(read_data=invalid_data)):
        app.loadFile("dummy_path.txt")

    # Проверяем, что статусная строка показывает сообщение об ошибке
    assert "Некорректные координаты в строке:" in app.statusBar.currentMessage()


def test_save_file(app, qtbot):
    """Тест сохранения файла с добавленными элементами."""
    # Добавление элементов
    app.drawPoint([100, 100])
    app.drawLine([200, 200, 300, 300])

    # Мок функции открытия для тестирования сохранения файла
    with patch("builtins.open", mock_open()) as mocked_file:
        app.file_path = "test_output.txt"
        app.saveFile()
        mocked_file.assert_called_once_with("test_output.txt", "w", encoding="utf-8")

        # Проверка, что корректные данные были записаны
        handle = mocked_file()
        handle.write.assert_any_call("100 100\n")
        handle.write.assert_any_call("200 200 300 300\n")
