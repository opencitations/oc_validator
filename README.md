# oc_validator

**oc_validator** is a Python (≥3.9) library to validate CSV documents storing citation data and bibliographic metadata.
To be processed by the validator, the tables must be built as either CITS-CSV or META-CSV tables, defined in two specification documents[^1][^2].

[^1]: Massari, Arcangelo, and Ivan Heibi. 2022. ‘How to Structure Citations Data and Bibliographic Metadata in the OpenCitations Accepted Format’. https://doi.org/10.48550/arXiv.2206.03971.

[^2]: Massari, Arcangelo. 2022. ‘How to Produce Well-Formed CSV Files for OpenCitations’. https://doi.org/10.5281/zenodo.6597141.

## Installation
The library can be installed from **pip**:
```
pip install oc_validator
```

## Usage

The validation process can be executed from the CLI by running the following command:

```bash
python -m oc_validator.main -i <input csv file path> -o <output dir path> [-m] [-s]
```

### Required Parameters

- `-i`, `--input`: The path to the CSV file to validate.
- `-o`, `--output`: The path to the directory where the output JSON file and .txt file will be stored.

### Optional Parameters

- `-m`, `--use-meta`: Enables the use of the OC Meta endpoint instead of external APIs to check if an ID exists (by checking if it is registered in OpenCitations Meta). If included, this option allows to fasten the whole process, since querying Meta is faster than querying external APIs, but results might not be the most up to date.
- `-s`, `--no-id-existence`: Skips the check for ID existence altogether, ensuring that neither the Meta endpoint nor any external APIs are used during validation. This allows for a much shorter execution time, but does not make sure that all the submitted IDs actually refer to real-world entities.

### Example Usage from CLI

To validate a CSV file and output the results to a specified directory (with optional parameters set to default values, i.e. checking for the existence of IDs via querying external APIs):

```bash
python -m oc_validator.main -i path/to/input.csv -o path/to/output_dir
```

To use OC Meta endpoint instead of external APIs to verify the existence of the IDs:

```bash
python -m oc_validator.main -i path/to/input.csv -o path/to/output_dir -m
```

To skip all ID existence verification:

```bash
python -m oc_validator.main -i path/to/input.csv -o path/to/output_dir -s
```

### Programmatic Usage

An object of the `Validator` class is instantiated, passing as parameters the path to the input document to validate and the path to the directory where to store the output. By calling the `validate()` method on the instance of `Validator`, the validation process gets executed.

The process automatically detects which of the two tables has been passed as input (on condition that the input CSV document's header is formatted correctly for at least one of them). During the process, the *whole* document is always processed: if the document is invalid or contains anomalies, the errors/warnings are reported in detail in a JSON file and summarized in a .txt file, which will be automatically created in the output directory. `validate` also returns a list of dictionaries corresponding to the JSON validation report (empty if the document is valid).

```python
from oc_validator.main import Validator

# Basic validation
v = Validator('path/to/table.csv', 'output/directory')
v.validate()

# Validation with Meta endpoint checking for ID existence
v = Validator('path/to/table.csv', 'output/directory', use_meta_endpoint=True)
v.validate()

# Validation skipping all ID existence checks
v = Validator('path/to/table.csv', 'output/directory', verify_id_existence=False)
v.validate()
```

Starting from version 0.3.3, it is possible to validate two tables at a time, one storing metadata and the other storing citations, in order to verify, besides all the other checks, that all the citations represented in a document have their metadata represented in the other document, and vice versa. This can be done by using the `ClosureValidator` class. The `ClosureValidator` class internally wraps two instances of `Validator`, one for metadata and one for citations, and requires to explicitly specify the table type for either document. Both the internal `Validator` instances can be separately customized by specifying the optional parameters for each of the two via the `meta_kwargs` and `cits_kwargs` arguments. `ClosureValidator` takes the following parameters:

- `meta_in`: Path to the input CSV table storing metadata.
- `meta_out_dir`: Directory for metadata validation results.
- `cits_in`: Path to the input CSV table storing citations.
- `cits_out_dir`: Directory for citation validation results.
- `meta_kwargs`: (Optional) Dictionary of configuration options for the metadata table validator.
- `cits_kwargs`: (Optional) Dictionary of configuration options for the citation table validator.

A usage example of how to validate metadata and citations with `ClosureValidator` is provided as follows:

```python
from oc_validator.main import ClosureValidator

cv = ClosureValidator(
    meta_in='path/to/meta.csv', 
    meta_out_dir='path/to/meta_results',
    cits_in='path/to/cits.csv', 
    cits_out_dir='path/to/cits_results',
    meta_kwargs={'verify_id_existence': False},  # Skip ID existence checks for metadata
    cits_kwargs={'use_meta_endpoint': True}  # Use OC Meta before external APIs to verify the existence of PIDs
)

cv.validate() # validates the tables and saves output files in the specified (separate) directories
```

## Output visualisation

`oc_validator` has an integrated tool for the interactive visualisation of the validation results, which helps users to locate the detected errors in the document in a more intuitive way, and facilitates human understanding of the underlying problems generating them. The documentation of the visualisation tool can be found in [oc_validator/interface/README.md](oc_validator/interface/README.md).