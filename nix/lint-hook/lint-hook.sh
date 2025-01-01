#shellcheck shell=bash
echo "Sourcing lint-hook.sh"

runLinter() {
    echo "Executing runLinter"
    ruff check --show-fixes --exit-non-zero-on-fix .
}

runFormatter() {
    echo "Executing runFormatter"
    ruff format --diff .
}

runTypeChecker() {
    echo "Executing runTypeChecker"
    basedpyright .
}

echo "Using lint-hook"
appendToVar preDistPhases runLinter runFormatter runTypeChecker
