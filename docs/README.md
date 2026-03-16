# Building Documentation

This directory contains the Sphinx documentation for RawlsianAgents.

## Prerequisites

Documentation dependencies are already included in the main project dependencies managed by `uv`. Make sure you've run:

```bash
uv sync
```

## Building HTML Documentation

To build the HTML documentation:

```bash
make html
```

This will generate the HTML documentation in the `_build/html/` directory.

Before building HTML, regenerate API stubs when public Python signatures,
docstrings, or state fields change:

```bash
uv run sphinx-apidoc --force --no-toc --separate -o docs/api src/rawlsianagents
```

This is especially relevant for negotiation workflow updates in
`src/rawlsianagents/negotiation_swarm.py`.

Open `_build/html/index.html` in your browser to view the documentation.

## Building Other Formats

Sphinx supports multiple output formats:

```bash
make latex    # LaTeX/PDF
make epub     # EPUB
make man      # Man pages
```

## Clean Build

To remove the build directory and start fresh:

```bash
make clean
```

## Documentation Structure

- `conf.py` - Sphinx configuration
- `index.rst` - Main documentation index
- `modules.rst` - API reference with autodoc
- `api/` - Individual API module documentation
- `_build/` - Generated documentation (ignored by git)
