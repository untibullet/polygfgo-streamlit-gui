import os

import streamlit as st
import subprocess
import psutil
from sympy import sympify, symbols

from cli_process import CLIProcess


CLI_PROCESS_NAME = "polygfgo_cli"


def parse_polynomial(polynomial: str) -> str:
    try:
        if "x" in polynomial:
            coefficients = sympify(polynomial.replace("^", "**")).as_poly(symbols('x')).all_coeffs()

            return " ".join(map(str, coefficients))

        coefficients = polynomial.split()
        coefficients = map(int, coefficients)  # Валидация записи

        return " ".join(map(str, coefficients))

    except Exception:
        raise Exception(f"Неверная запись многочлена: {polynomial}. Смотри доступные формы для записи")


def format_polynomial_to_alg(poly: str) -> str:
    coefficients = poly.lstrip("[").rstrip("]").split()

    result = ""
    for i, c in enumerate(coefficients):
        if i == len(coefficients) - 1:
            break
        if c == "0":
            continue
        result += f"{c}*x^{len(coefficients) - i - 1} + "
    result += coefficients[-1]

    return result


def format_polynomial_to_vec(poly: str) -> str:
    return poly.lstrip("[").rstrip("]")


def format_polynomial_to_cli(poly: str) -> str:
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


def mode_show_info():
    # Отображение логотипов Go и Streamlit
    logo_path = "style/Go_Streamlit_Merge.png"  # Локальный путь к картинке
    st.image(logo_path, use_container_width=True)  # Отображение логотипа проекта

    # Заголовок проекта
    st.title("Математические операции над многочленами в конечном поле GF(p^m)")

    # Описание проекта
    st.subheader("О проекте")
    st.markdown(
        """
        Это демонстрационное веб-приложение для работы с многочленами в конечных полях.
        Вы можете использовать его для выполнения следующих задач:

        - Генерация многочленов в конечных полях.
        - Арифметические операции над многочленами.
        - Тестирование на неприводимость заданного многочлена.

        Приложение предназначено как для образовательных, так и для исследовательских целей.
        """
    )

    # Инструкция для пользователя
    st.subheader("Инструкция по эксплуатации")
    st.markdown(
        """
        1. Выберите нужный **режим работы** приложения и **форму представления многочленов** на _**боковой панели**_ (слева).
        2. Задайте необходимые параметры конечного поля и многочленов. Например:
           - **Основание поля** (простое число).
           - **Степень расширения поля**.
           - **Неприводимый многочлен**.
           - **Степень многочленов**.
        3. Используйте доступные функции для выполнения операций.
        4. Результаты отображаются на странице в текстовом виде.
        5. При необходимости сохраните результат в виде файла или скопируйте данные через доступные кнопки.
        """
    )

    # Пример вызова функциональности
    st.subheader("Пример использования")
    st.code(
        """
        Поле GF(3^2)
        Операция: (x^2 + 2x + 1) + (x + 2) = x^2 + 3x + 3 = x^2
        """, language="plaintext"
    )

    # Призыв к действию
    st.info("Используйте боковую панель для выбора режима работы!")


def mode_basic_operations():
    # Ввод характеристик поля
    st.header("Характеристики конечного поля")
    prime = st.number_input("Введите основание поля (простое число)", min_value=2, step=1, value=2)
    degree = st.number_input("Введите степень поля", min_value=1, step=1, value=1)

    irreducible_poly = st.text_input(
        "Опционально введите неприводимый многочлен (коэффициенты через пробел, например, '1 0 1' для x^2 + 1):"
    )

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
                command += " " + format_polynomial_to_cli(parse_polynomial(irreducible_poly))

            # Отключили логирование
            command += " off"

            # Отправляем команду в процесс
            cli_process.stdin.write(command + "\n")
            cli_process.stdin.flush()

            # Читаем ответ от процесса
            result = cli_process.stdout.readline().strip()

            if "created" in result:
                # Вывод положительного сообщения
                st.success(f"Поле задано")
            else:
                raise Exception(result)

        except Exception as e:
            st.error(f"Произошла ошибка: {e}")

    # Ввод операции
    st.header("Выбор операции")
    operation = st.selectbox("Выберите арифметическую операцию", ["Сложить", "Вычесть", "Умножить", "Разделить", "НОД"])

    operations = {
        "Сложить": "add",
        "Вычесть": "sub",
        "Умножить": "mul",
        "Разделить": "div",
        "НОД": "gcd"
    }

    # Ввод многочленов
    st.header("Ввод многочленов")
    st.write("Введите коэффициенты многочленов через пробел, начиная с коэффициента при старшей степени.")

    poly1_input = st.text_input("Многочлен 1:", "1 0 1" if formating_flag == 0 else "1*x^2+1")
    poly2_input = st.text_input("Многочлен 2:", "1 1" if formating_flag == 0 else "1*x^1+1")

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
                    format_polynomial_to_cli(parse_polynomial(poly1_input)),
                    format_polynomial_to_cli(parse_polynomial(poly2_input))
                ]
            )

            # Отправляем команду в процесс
            cli_process.stdin.write(command + "\n")
            cli_process.stdin.flush()

            # Читаем ответ от процесса
            result = str(cli_process.stdout.readline().strip())

            if "No field created" in result:
                st.error(f"Произошла ошибка: Поле не создано")
                return

            # Вывод результата операции
            if operations[operation] == "div":
                quo, rem = result.lstrip("[").rstrip("]").split("] [")
                quo = format_polynomial_to_vec(quo) if formating_flag == 0 else format_polynomial_to_alg(quo)
                rem = format_polynomial_to_vec(rem) if formating_flag == 0 else format_polynomial_to_alg(rem)
                st.text("Частное:")
                st.code(quo, language="plaintext")
                st.text("Остаток:")
                st.code(rem, language="plaintext")
            else:
                st.code(
                    format_polynomial_to_vec(result) if formating_flag == 0 else format_polynomial_to_alg(result),
                    language="plaintext"
                )

        except Exception as e:
            st.error(f"Произошла ошибка: {e}")


def mode_generation():
    # Ввод параметров
    st.header("Параметры генерации многочленов")

    st.warning("Внимание! Максимальное значение характеристики q = p^m = 2^61.")

    output_type = st.selectbox("Выберите форму ответа:", [
        "Отображение на странице",
        "Запись в txt файл"
    ])

    base = st.number_input("Введите основание поля (простое число):", min_value=2, value=3)

    degree = st.number_input("Введите степень многочленов:", min_value=1, value=2)

    limit = 128 if output_type == "Отображение на странице" else 1024
    count = st.number_input(
        "Введите количество многочленов (макс. для отображения на странице 128 шт.):",
        min_value=0,
        max_value=limit,
        value=10
    )
    count = min(count, limit)

    cli_process = st.session_state.cli_process # Сохраненный процесс

    if st.button("Найти"):
        # Заголовок для результата
        st.header("Результат генерации")
        try:
            if cli_process.poll() is not None:
                error_output = cli_process.stderr.read().strip()
                raise Exception(f"CLI-утилита завершилась при запуске. Ошибка: {error_output}")

            # Подготовка команды для консольной утилиты
            command = f"gen {base} {degree} {count}"

            # Отправляем команду в процесс
            cli_process.stdin.write(command + "\n")
            cli_process.stdin.flush()

            # Читаем ответ от процесса
            result = str(cli_process.stdout.readline().strip())

            if "degree" in result:
                raise Exception(f"Слишком большое значение расширения поля q = p^m = {base}^{degree}")

            if output_type == "Отображение на странице":
                while result != "-1":
                    result = format_polynomial_to_vec(result) if formating_flag == 0 else format_polynomial_to_alg(
                        result)
                    st.code(result, language="plaintext")
                    result = cli_process.stdout.readline().strip()
            else:
                file = open("user_output.txt", "w")
                while result != "-1":
                    result = format_polynomial_to_vec(result) if formating_flag == 0 else format_polynomial_to_alg(
                        result)
                    file.write(result + '\n')
                    result = cli_process.stdout.readline().strip()
                file.close()
                # Получаем информацию о файле
                file_size = os.path.getsize("user_output.txt")  # Размер в байтах
                # Отображаем информацию о файле
                st.write(f"Размер файла: `{file_size} байт`")
                data = open("user_output.txt", "r")
                st.download_button(
                    label="Скачать файл",
                    data=data,
                    file_name="generation.txt",
                    mime="text/plain"
                )
                data.close()

        except Exception as e:
            st.error(f"Произошла ошибка: {e}")


def mode_irreducible_test():
    # Ввод параметров
    st.header("Параметры теста")

    st.warning("Внимание! Максимальное значение характеристики q = p^m = 2^61.")

    base = st.number_input("Введите основание поля (простое число):", min_value=2, value=3)

    poly = st.text_input("Введите многочлен :", "1 0 1" if formating_flag == 0 else "1*x^2 + 1")

    cli_process = st.session_state.cli_process  # Сохраненный процесс

    if st.button("Тест"):
        try:
            if cli_process.poll() is not None:
                error_output = cli_process.stderr.read().strip()
                raise Exception(f"CLI-утилита завершилась при запуске. Ошибка: {error_output}")

            # Подготовка команды для консольной утилиты
            command = f"irreducible {format_polynomial_to_cli(parse_polynomial(poly))} {base}"

            # Отправляем команду в процесс
            cli_process.stdin.write(command + "\n")
            cli_process.stdin.flush()

            # Читаем ответ от процесса
            result = cli_process.stdout.readline().strip()
            if result == "true":
                st.write("Многочлен НЕПРИВОДИМ в заданном поле")
            elif result == "false":
                st.write("Многочлен ПРИВОДИМ в заданном поле")
            else:
                st.error(f"{result}")

        except Exception as e:
            st.error(f"Произошла ошибка: {e}")


# ----------------------ENTRYPOINT----------------------
# Загружаем CSS из файла
with open("style/go_theme.css") as css_file:
    st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)

modes = ["Информация о проекте", "Стандартные операции", "Генерация неприводимых многочленов", "Тест на неприводимость"]

st.sidebar.title("POLY-GF-GO")

# Добавляем виджет RadioButton в боковую панель
mode = st.sidebar.selectbox("Выберите режим работы:", modes)

polynomials_form = st.sidebar.radio("Выберите форму представления многочленов:", [
    "Алгебраическая форма",
    "Вектор коэффициентов"
])

formating_flag = {
    "Алгебраическая форма": 1,
    "Вектор коэффициентов": 0
}[polynomials_form]

# Заголовок боковой панели
st.sidebar.header(".log файл текущей сессии")

# Путь к файлу
log_path = "errors.log"

# Инициализация процесса в Session State
if "cli_process" not in st.session_state:
    if os.path.exists(log_path):
        os.remove(log_path)

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

try:
    # Проверяем существование файла
    if os.path.exists(log_path):
        # Получаем информацию о файле
        file_size = os.path.getsize(log_path)  # Размер в байтах

        # Отображаем информацию о файле
        st.sidebar.write(f"Размер файла: `{file_size} байт`")

        # Открываем файл для чтения и добавляем кнопку для скачивания
        with open(log_path, "r") as f:
            st.sidebar.download_button(
                label="Скачать",
                data=f,
                file_name="errors.log",
                mime="text/plain"
            )
    else:
        st.sidebar.info("Файл errors.log не найден. Начните работу")
except Exception as e:
    st.sidebar.error(f"Ошибка при обработке файла: {e}")

if mode == "Информация о проекте":
    mode_show_info()
elif mode == "Стандартные операции":
    mode_basic_operations()
elif mode == "Генерация неприводимых многочленов":
    mode_generation()
elif mode == "Тест на неприводимость":
    mode_irreducible_test()
