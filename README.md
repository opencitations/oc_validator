# oc_validator

**oc_validator** is a Python (≥3.9) library to validate CSV documents storing citation data and bibliographic metadata.
To be processed by the validator, the tables must be built as either CITS-CSV or META-CSV tables, defined in two
specification documents[^1][^2].

[^1]: Massari, Arcangelo, and Ivan Heibi. 2022. ‘How to Structure Citations Data and Bibliographic Metadata in the OpenCitations Accepted Format’. https://doi.org/10.48550/arXiv.2206.03971.

[^2]: Massari, Arcangelo. 2022. ‘How to Produce Well-Formed CSV Files for OpenCitations’. https://doi.org/10.5281/zenodo.6597141.

## Installation
The library can be installed from **pip**:
```
pip install oc_validator
```

## Usage
The validation process can be executed from the CLI, by running the following command:
```
python -m oc_validator.main -i <input csv file path> -o <output dir path>
```

An object of the `Validator` class is instantiated, passing as parameters the path to the input document to validate and the 
path to the directory where to store the output. By calling the `validate()` method on the instance of `Validator`,
the validation process gets executed.

The process automatically detects which of the two tables has been passed as input (on condition that the input 
CSV document's header is formatted correctly for at least one of them). During the process, the *whole* document is always processed: 
if the document is invalid or contains anomalies, the errors/warnings are reported in detail in a JSON file
and summarized in a .txt file, which will be automatically created in the output directory. `validate` also returns a list
of dictionaries corresponding to the JSON validation report (empty if the document is valid).

```
v = Validator('path/to/table.csv', 'output/directory')
v.validate()
```

