# CSV Reader

This is a simple helper to read and write CSV files.

## Example

```py
from nupd.inputs.csv import CsvInput

csv = CsvInput[MyEntryInfo](Path("input-file.csv"))

entry_infos = csv.read(lambda x: MyEntryInfo(**x))
csv.write(entries_info, serialize=lambda x: x.model_dump(mode="json"))
```

## API reference

::: nupd.inputs.csv.CsvInput
