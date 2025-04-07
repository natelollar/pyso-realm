# ruff linter
ruff check --select=ALL --fix $args[0]
# ruff formatter
ruff format $args[0]