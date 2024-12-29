# Contributing

## Setup

To begin contributing to Androguard:

1.  Clone Androguard:
```bash
git clone https://github.com/androguard/androguard.git
```

2.  Install `poetry`:
```bash
pip3 install poetry
```

3.  Install Androguard:
```bash
poetry install
```

4.  Verify successful installation by running the unit tests.  From the Androguard root directory:
```bash
poetry run python -m unittest discover -s tests -p 'test_*.py'
```

5.  Building docs (optional):
```bash
cd docs && pip3 install -r requirements.docs.txt
mkdocs serve
```

## Standards

* Functions and classes should include [typing](https://docs.python.org/3/library/typing.html) annotations to help navigate and auto-document the code
* Functions and classes should be documented using [sphinx](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html) style docstrings.  When referencing other Androguard-internal functions and classes, docstring bodies should use the following syntax to ensure cross-reference link generation.  For example, to generate a cross-reference link to the `ClassAnalysis` class, use the following bracket annotation that indicates its package:

```python
class REF_TYPE(IntEnum):
    """
    Stores the opcodes for the type of usage in an XREF.

    Used in [ClassAnalysis][androguard.core.analysis.analysis.ClassAnalysis] to store the type of reference to the class.
    """
```