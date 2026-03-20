#shellcheck shell=bash
echo "Sourcing lint-hook.sh"

runFormatter() {
    echo "Executing runFormatter"
    ruff format --diff .
}

runLinter() {
    echo "Executing runLinter"
    ruff check --show-fixes --exit-non-zero-on-fix .
}

runTypeChecker() {
    echo "Executing runTypeChecker"
    basedpyright .
}

echo "Using lint-hook"
appendToVar preDistPhases runFormatter runLinter runTypeChecker
