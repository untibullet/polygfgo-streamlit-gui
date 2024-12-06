import streamlit as st
import subprocess
import psutil

from cli_process import CLIProcess


CLI_PROCESS_NAME = "polygfgo_cli"


# Форматирование полинома
def format_polynomial(poly: str) -> str:
    return poly.strip().replace(" ", ",")


def terminate_previous_processes():
    for proc in find_processes_by_name(CLI_PROCESS_NAME):
        proc.terminate()
        proc.wait()


def find_processes_by_name(name):
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Проверяем, содержит ли имя процесса искомую строку
            if name.lower() in proc.name().lower():
                processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # Игнорируем процессы, к которым нет доступа
    return processes


# Загружаем CSS из файла
with open("style/go_theme.css") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

# Отображение логотипов Go и Streamlit
logo_path = "style/Go_Streamlit_Merge.png"  # Локальный путь к картинке
st.image(logo_path, width=1200)

# Заголовок страницы
st.title("Арифметические операции над многочленами в конечном поле GF(p^m)")
st.write("Демонстрация работы библиотеки для операций над многочленами в конечных полях.")

# Ввод характеристик поля
st.header("Характеристики конечного поля")
prime = st.number_input("Введите характеристику поля (простое число)", min_value=2, step=1, value=2)
degree = st.number_input("Введите степень поля", min_value=1, step=1, value=1)

irreducible_poly = st.text_input(
    "Опционально введите неприводимый многочлен (коэффициенты через пробел, например, '1 0 1' для x^2 + 1):"
)

# Инициализация процесса в Session State
if "cli_process" not in st.session_state:
    terminate_previous_processes()
    st.session_state.cli_process = CLIProcess(
        [f"./bin/{CLI_PROCESS_NAME}"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    _ = st.session_state.cli_process.stdout.readline().strip()

cli_process = st.session_state.cli_process  # Используем сохранённый процесс

if st.button("Задать поле"):
    try:
        if cli_process.poll() is not None:
            error_output = cli_process.stderr.read().strip()
            raise Exception(f"CLI-утилита завершилась при запуске. Ошибка: {error_output}")

        # Подготовка команды для консольной утилиты
        command = f"field {prime} {degree}"

        # Добавили неприводимый полином
        if irreducible_poly:
            command += " " + format_polynomial(irreducible_poly)

        # Отключили логирование
        command += " off"

        # Отправляем команду в процесс
        cli_process.stdin.write(command + "\n")
        cli_process.stdin.flush()

        # Читаем ответ от процесса
        result = cli_process.stdout.readline().strip()

        # Вывод результата операции
        st.success(f"Результат операции: {result}")

    except Exception as e:
        st.error(f"Произошла ошибка: {e}")

# Ввод операции
st.header("Выбор операции")
operation = st.selectbox("Выберите арифметическую операцию", ["Сложить", "Вычесть", "Умножить", "Разделить"])

operations = {
    "Сложить": "add",
    "Вычесть": "sub",
    "Умножить": "mul",
    "Разделить": "div"
}

# Ввод многочленов
st.header("Ввод многочленов")
st.write("Введите коэффициенты многочленов через пробел, начиная с коэффициента при старшей степени.")

poly1_input = st.text_input("Многочлен 1:", "1 0 1")
poly2_input = st.text_input("Многочлен 2:", "1 1")

# Кнопка для выполнения операции
if st.button("Выполнить операцию"):
    try:
        if cli_process.poll() is not None:
            error_output = cli_process.stderr.read().strip()
            raise Exception(f"CLI-утилита завершилась при запуске. Ошибка: {error_output}")

        # Подготовка команды для консольной утилиты
        command = " ".join(
            [
                operations[operation],
                format_polynomial(poly1_input),
                format_polynomial(poly2_input)
            ]
        )

        # Отправляем команду в процесс
        cli_process.stdin.write(command + "\n")
        cli_process.stdin.flush()

        # Читаем ответ от процесса
        result = cli_process.stdout.readline().strip()

        if "No field created" in result:
            st.error(f"Произошла ошибка: Поле не создано.")
        else:
            # Вывод результата операции
            st.text(f"Результат операции: {result}")

    except Exception as e:
        st.error(f"Произошла ошибка: {e}")
