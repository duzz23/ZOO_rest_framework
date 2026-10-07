#!/usr/bin/env python3
"""
Скрипт для запуска тестов с отображением статистики и покрытия кода.

Использование:
    python run_tests.py
    
Покажет:
- Общее количество тестов
- Количество прошедших/упавших/ошибочных тестов
- Процент покрытия кода тестами
- Детальный отчёт по покрытию по каждому файлу
"""

import os
import sys
import subprocess
import re
from pathlib import Path

# Пути
PROJECT_ROOT = Path(__file__).parent
VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
MANAGE_PY = PROJECT_ROOT / "manage.py"

# Модули для покрытия (ai_agent исключён из-за segfault HuggingFace при instrument)
MODULES_TO_COVER = [
    "mainapp.models",
    "mainapp.views",
    "mainapp.forms",
    "mainapp.admin",
    "mainapp.tasks",
    "api.models",
    "api.serializers",
    "api.views",
    "api.filters",
    "api.permission",
]

# Django test modules (TestCase)
DJANGO_TEST_MODULES = [
    "mainapp.tests.test_models",
    "mainapp.tests.test_views",
    "mainapp.tests.test_ai_chat",
    "api.tests.test_api",
    "ai_agent.tests.test_services_unittest",
]

# pytest modules
PYTEST_MODULES = [
    "ai_agent/tests/test_services_pytest.py",
]


def run_tests():
    """Запуск тестов с coverage и выводом статистики."""
    
    print("=" * 80)
    print("🧪 ЗАПУСК ТЕСТОВ С ПОКРЫТИЕМ КОДА")
    print("=" * 80)
    print()
    
    # Собираем команды для coverage
    modules_arg = ",".join(MODULES_TO_COVER)
    
    cmd = [
        str(VENV_PYTHON),
        str(MANAGE_PY),
        "test",
        *DJANGO_TEST_MODULES,
        "-v", "2",
        "--keepdb"
    ]
    
    print(f"📋 Запуск команд: {' '.join(cmd)}")
    print()
    
    # Запускаем тесты
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Парсим результаты тестов
    output = result.stdout + result.stderr
    
    # Считаем тесты
    total_match = re.search(r"Ran (\d+) tests?", output)
    total_tests = int(total_match.group(1)) if total_match else 0
    
    # Считаем passed
    passed_match = re.findall(r"\.\.\. ok$", output, re.MULTILINE)
    passed = len(passed_match)
    
    # Считаем failed
    failed_match = re.findall(r"\.\.\. FAIL$", output, re.MULTILINE)
    failed = len(failed_match)
    
    # Считаем errors
    error_match = re.findall(r"\.\.\. ERROR$", output, re.MULTILINE)
    errors = len(error_match)
    
    # Считаем skipped
    skipped_match = re.findall(r"\.\.\. SKIP$", output, re.MULTILINE)
    skipped = len(skipped_match)
    
    # Выводим статистику тестов
    print("\n" + "=" * 80)
    print("📊 СТАТИСТИКА ТЕСТОВ")
    print("=" * 80)
    print(f"  ✅ Прошло успешно:  {passed}")
    print(f"  ❌ Упало:           {failed}")
    print(f"  ⚠️  Ошибки:          {errors}")
    print(f"  ⏭️  Пропущено:       {skipped}")
    print(f"  📈 Всего тестов:    {total_tests}")
    print()
    
    if failed > 0:
        print("  🚨 УПАВШИЕ ТЕСТЫ:")
        print("  " + "-" * 76)
        for line in output.split('\n'):
            if 'FAIL:' in line and 'test_' in line:
                print(f"  ❌ {line.strip()}")
        print()
    
    if errors > 0:
        print("  🚨 ТЕСТЫ С ОШИБКАМИ:")
        print("  " + "-" * 76)
        for line in output.split('\n'):
            if 'ERROR:' in line and 'test_' in line:
                print(f"  ⚠️  {line.strip()}")
        print()
    
    # Покрытие кода
    print("=" * 80)
    print("📈 ПОКРЫТИЕ КОДА ТЕСТАМИ")
    print("=" * 80)
    
    # Запускаем coverage для покрытия
    omit_patterns = [
        "*/migrations/*",
        "*/tests/*",
        "*/__pycache__/*",
        "manage.py",
        "wsgi.py",
        "asgi.py",
        "run_tests.py",
    ]
    omit_args = []
    for pat in omit_patterns:
        omit_args.extend(["--omit", pat])
    
    cov_cmd = [
        str(VENV_PYTHON),
        "-m", "coverage", "run",
        f"--source={modules_arg}",
        *omit_args,
        str(MANAGE_PY),
        "test",
        *DJANGO_TEST_MODULES,
        "--keepdb"
    ]
    
    print("\n⏳ Измерение покрытия кода...")
    cov_result = subprocess.run(cov_cmd, capture_output=True, text=True)
    if cov_result.returncode != 0:
        print(f"  ⚠️ Coverage error (returncode={cov_result.returncode}):")
        print(cov_result.stderr[:500] if cov_result.stderr else "(no stderr)")
        print(cov_result.stdout[:500] if cov_result.stdout else "(no stdout)")
    
    # Генерируем текстовый отчёт
    report = subprocess.run(
        [str(VENV_PYTHON), "-m", "coverage", "report", "--show-missing"],
        capture_output=True,
        text=True
    )
    
    print(report.stdout)
    
    # Парсим общее покрытие из строки TOTAL
    # Формат: TOTAL 286 9 97% (Stmts Miss Cover)
    coverage_percent = 0
    total_covered = 0
    total_missed = 0
    for line in report.stdout.split('\n'):
        if line.strip().startswith('TOTAL'):
            parts = line.split()
            if len(parts) >= 4:
                try:
                    total_covered = int(parts[1])
                    total_missed = int(parts[2])
                    coverage_percent = float(parts[3].replace('%', ''))
                    break
                except (ValueError, IndexError):
                    continue
    
    if coverage_percent > 0:
        total_lines = total_covered + total_missed
        print("\n" + "=" * 80)
        print("🎯 ИТОГО")
        print("=" * 80)
        print(f"  📊 Покрытие кода: {coverage_percent:.1f}% ({total_covered} строк покрыто из {total_lines})")
        print()
        
        # Оценка покрытия
        if coverage_percent >= 85:
            print("  🟢 Отличное покрытие! Цель достигнута (≥85%)")
        elif coverage_percent >= 70:
            print("  🟡 Хорошее покрытие, но можно улучшить")
        elif coverage_percent >= 50:
            print("  🟡 Среднее покрытие, требуется доработка")
        else:
            print("  🔴 Низкое покрытие, необходимо значительно улучшить")
        
        print()
    
    # Покрытие по файлам
    print("\n" + "=" * 80)
    print("📁 ПОКРЫТИЕ ПО ФАЙЛАМ (детально)")
    print("=" * 80)
    
    files_report = subprocess.run(
        [str(VENV_PYTHON), "-m", "coverage", "report", "--show-missing"],
        capture_output=True,
        text=True
    )
    
    print(files_report.stdout)
    
    # Запускаем pytest для pytest-тестов
    print("\n" + "=" * 80)
    print("🔍 ЗАПУСК PYTEST")
    print("=" * 80)
    
    pytest_cmd = [
        str(VENV_PYTHON),
        "-m", "pytest",
        *PYTEST_MODULES,
        "-v",
        "--tb=short"
    ]
    
    print(f"\n📋 Запуск: {' '.join(pytest_cmd)}")
    print()
    
    pytest_result = subprocess.run(pytest_cmd)
    pytest_passed = pytest_result.returncode == 0
    
    # Итоговый статус
    print("\n" + "=" * 80)
    if failed == 0 and errors == 0 and pytest_passed:
        print("✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
    else:
        total_issues = failed + errors
        if not pytest_passed:
            total_issues += 1
            print(f"⚠️  PYTEST: ОБНАРУЖЕНЫ ПРОБЛЕМЫ В ТЕСТАХ PYTEST")
        print(f"⚠️  ОБНАРУЖЕНО ПРОБЛЕМ: {total_issues}")
    print("=" * 80)
    
    return 0 if (failed == 0 and errors == 0 and pytest_passed) else 1


if __name__ == "__main__":
    sys.exit(run_tests())
