# Terminology

- The library — this package.
- An updater script — this is what you would run to add/update plugins in
  specific ecosystems.
- An input — list of references to the outputs. As an example, for Vim plugins,
  this would be a CSV table with GitHub URLs and other data.
- An output — what is generated at the end. This can be for example a plugin or
  an extension.
- An entry — a single unit of what updater updates. For Vim plugins this would
  be a plugin, for Gnome extensions this would be an extension.
- `G` prefix means it is a [Generic](https://typing.python.org/en/latest/reference/generics.html).
