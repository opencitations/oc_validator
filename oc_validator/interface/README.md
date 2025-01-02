# Validation Output Visualiser

The `interface` package provides tools to visualise the output of the validation process via a graphical interface (HTML document). This helps users to easily identify and understand the errors in the validated CSV tables.

## Usage from CLI

To visualise the output of the validation via a graphical interface, you can run the following command on the CLI:

```bash
python -m oc_validator.interface.run_gui -t <path to CSV table> -r <path to the JSON validation report> -o <path to the output HTML file>
```

This command will create an HTML file for visualising the validation results, and store it in the specified directory.

## Programmatic Usage

The process of creating a GUI for the validation output consists mainly of the execution of a function, `make_gui`,  which takes as input the filepath to the CSV data, the filepath to the JSON validation report, and the filepath where to save the HTML visualisation. This function manages only one dataset at a time (the user must make sure that CSV table and the JSON validation report refer to the same data). To visualise in an interactive GUI the validation results of two different documents, e.g. metadata and citations, use the `merge_html_files` function.


### `make_gui`

Generates an HTML document to visualise the validation results.

```python
from oc_validator.interface.gui import make_gui

make_gui(csv_path, report_path, output_html_path)
```

- `csv_path`: Path to the original CSV table containing data.
- `report_path`: Path to the JSON report storing the detailed validation output.
- `output_html_path`: Path to the output HTML file.

#### Example

```python
from oc_validator.interface.gui import make_gui

csv_path = 'path/to/table.csv'
report_path = 'path/to/report.json'
output_html_path = 'path/to/output.html'

make_gui(csv_path, report_path, output_html_path)
```

This example will generate an HTML file at `output_html_path` that visualises the validation results of the CSV file located at `csv_path` using the validation report at `report_path`.

### `merge_html_files`

Merges two HTML files into one. Particularly useful if there is a need to visualise the output of both metadata and citation data in the same file (i.e. if we need to visualise the report obtained by running the `validate()` method of the `oc_validator.main.ClosureValidator` class).

```python
from oc_validator.interface.gui import merge_html_files

merge_html_files(doc1_fp, doc2_fp, merged_out_fp)
```

- `doc1_fp`: Path to the first HTML document.
- `doc2_fp`: Path to the second HTML document.
- `merged_out_fp`: Path to the output merged HTML document.

#### Example

```python
from oc_validator.interface.gui import merge_html_files

doc1_fp = 'path/to/first_document.html'
doc2_fp = 'path/to/second_document.html'
merged_out_fp = 'path/to/merged_output.html'

merge_html_files(doc1_fp, doc2_fp, merged_out_fp)
```

This example will merge the HTML files located at `doc1_fp` and `doc2_fp` into a single HTML file at `merged_out_fp`. 

## Example Workflow

Here is an example workflow that demonstrates how to use both `make_gui` and `merge_html_files` functions together:

```python
from oc_validator.interface.gui import make_gui, merge_html_files

# Paths to input files
meta_data = 'path/to/meta_table.csv'
cits_data = 'path/to/cits_table.csv'
report_meta = 'path/to/report_meta.json'
report_cits = 'path/to/report_cits.json'
output_html_meta = 'path/to/output_meta.html'
output_html_cits = 'path/to/output_cits.html'
merged_output_html_path = 'path/to/merged_output.html'

# Generate the first HTML visualisation (e.g. for metadata)
make_gui(meta_data, report_meta, output_html_meta)

# Generate the second HTML visualisation (could be for another CSV and report)
make_gui(cits_data, report_cits, output_html_cits)

# Merge the two HTML visualisations into one
merge_html_files(output_html_meta, output_html_cits, merged_output_html_path)
```

This workflow will generate two separate HTML visualisations and then merge them into a single HTML file.

## Source Code

The source code for the visualisation process is in [`gui.py`](gui.py).
