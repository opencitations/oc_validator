from oc_validator.interface.gui import make_gui
from argparse import ArgumentParser


if __name__ == '__main__':

    parser = ArgumentParser(description='Show a visual interface for easily identifying the errors in the validated table.')
    parser.add_argument('-t', '--table-fp', type=str, required=True, help='Path to the original CSV table containing data.')
    parser.add_argument('-r', '--report-fp', type=str, required=True, help='Path to the JSON report storing the detailed validation output.')
    parser.add_argument('-o', '--out-fp', type=str, required=True, help='Path to the output HTML file.')

    args = parser.parse_args()

    csv_path = args.table_fp
    report_path = args.report_fp
    output_html_path = args.out_fp

    make_gui(csv_path, report_path, output_html_path)