# Developer tools

These tools were useful during the build-out and may help with future application changes. Run them from the repository root with uv. Generated files stay outside Git.

| Module | Summary |
| --- | --- |
| `compare_sites.py` | Captures browser observations and screenshots, compares pages with saved references, and reports differences for review. Some modes contact websites and write files. |
| `__init__.py` | Marks this directory as an importable Python package for the comparison tool and its tests. |

[Browser comparison](../docs/browser_comparison.md) gives commands and limits. Retired capture/validator modules are preserved in [conversion history](../historical_conversion_info/code/README.md).
