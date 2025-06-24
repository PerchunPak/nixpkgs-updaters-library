{
  makePythonHook,
  ruff,
  basedpyright,
  joblib-stubs,
}:
makePythonHook {
  name = "lint-hook";
  propagatedBuildInputs = [
    basedpyright
    ruff
    joblib-stubs
  ];
} ./lint-hook.sh
