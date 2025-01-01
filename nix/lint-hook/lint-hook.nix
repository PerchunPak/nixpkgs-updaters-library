{
  makePythonHook,
  ruff,
  basedpyright,
}:
makePythonHook {
  name = "lint-hook";
  propagatedBuildInputs = [
    basedpyright
    ruff
  ];
} ./lint-hook.sh
