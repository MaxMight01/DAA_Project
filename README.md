# DAA Project — Question 12: Optimal Military Troupe Stationing on a Tree

The towns and roads of country XYZ form a tree on `n` towns. Each town is
assigned `0`, `1`, or `2` troupes so that every town assigned `0` troupes has a
neighbour assigned `2` troupes, and the total number of troupes is minimised.
The solution is a linear-time dynamic program on the rooted tree; the report
contains the algorithm, its correctness proof, and the complexity analysis.

## Contents

| File | Description |
| --- | --- |
| `RAMDAS_SINGH_SATHVIK_HS_DAA_PROJECT.pdf` | The project report. |
| `RAMDAS_SINGH_SATHVIK_HS_DAA_PROJECT.tex` | LaTeX source of the report. |
| `troupes.py` | The implementation: the dynamic program, optimal-assignment reconstruction, a brute-force reference solver, three random-tree generators, and a verification suite. |
| `daa_proj.ipynb` | The notebook used during development: the three generators with their complexity analyses, the recursive and iterative dynamic programs, and the timing and averaging experiments. |
| `Project_Questions.pdf` | The original list of project questions. |

## Requirements

Python 3.8 or later. Only the standard library is used; no external packages are
required.

## Running `troupes.py`

Run the following from this directory.

```bash
python troupes.py --demo
```
Prints an optimal assignment for a sample path and a sample star.

```bash
python troupes.py --verify
```
Runs the verification suite. The dynamic program is checked against the
exhaustive `O(3^n)` solver over every labelled tree for `n` up to `6` and over
random trees from all three generators for `7 <= n <= 10`. Each reconstructed
assignment is confirmed to be feasible and of optimal cost.

```bash
python troupes.py --ratio 5000 --trials 300
```
Reports the average value of `OPT / n` over random trees on `n` towns.

### Using it as a library

Trees are stored as 1-indexed adjacency lists (`adj[0]` is unused; the towns are
`1, ..., n`).

```python
from troupes import min_troupes, min_troupes_assignment

adj = [[], [2], [1, 3], [2, 4], [3, 5], [4]]   # the path 1-2-3-4-5
min_troupes(adj)                 # 4
cost, f = min_troupes_assignment(adj)
# cost == 4, f == [0, 2, 0, 0, 2, 0]; f[v] is the number of troupes at town v
```

## Running the notebook `daa_proj.ipynb`

### Prerequisites

Install the following.

- [Python](https://www.python.org/downloads/)
- [Visual Studio Code](https://code.visualstudio.com/download)

In VS Code, open the Extensions view (`Ctrl + Shift + X`) and install:

- Python (by Microsoft)
- Jupyter (by Microsoft)

### Steps

1. Open VS Code and choose **File → Open Folder**, then select this folder.
2. Open `daa_proj.ipynb` from the Explorer panel.
3. Select a Python kernel when prompted.
4. Click **Run All** to execute every cell, or run the cells in order.

The outputs appear below each cell. If the Python interpreter or the Jupyter
kernel is not detected, verify that Python is installed and select an installed
Python environment as the kernel.

## Rebuilding the report

```bash
pdflatex RAMDAS_SINGH_SATHVIK_HS_DAA_PROJECT.tex
pdflatex RAMDAS_SINGH_SATHVIK_HS_DAA_PROJECT.tex
```
The source reads `../../public/macros.tex`, so compile it from this directory.
Two passes are needed to resolve the cross-references.
