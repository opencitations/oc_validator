# Validation output visualiser

To visualise the output of the validation via graphical interface (HTML document) you can run the following command:

```
python -m run_gui -t <path to CSV table> -r <path to the JSON validation report> -o <path to the output HTML file>
```

The process will output an HTML document (whether or not the CSV table is valid) and directly open a tab on the default browser to show its rendered, interactive version.

Source code for the process in `run_gui.py` is in `gui.py`.