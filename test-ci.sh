#!/bin/bash
# Встановлення uv відповідно до нової конфігурації
curl -LsSf https://astral.sh/uv/install.sh | sh
# Виведення версії для перевірки
~/.local/bin/uv --version
