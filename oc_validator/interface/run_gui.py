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

"""
USAGE EXAMPLE


meta_in = '../data/meta_sample.csv'   # META-CSV table filepath
meta_out_dir = '../results/meta'
cits_in = '../data/cits_sample.csv'  # CITS-CSV table filepath
cits_out_dir = '../results/cits'

# Validate both documents, check that there is a transitive closure (the options specified avoid the verification of the existence of external IDs for both documents)
cv = ClosureValidator(meta_in, meta_out_dir, cits_in, cits_out_dir, meta_kwargs={'verify_id_existence':False}, cits_kwargs={'verify_id_existence':False})
cv.validate()

# Create two separate HTML documents for visualising the validation reports of META-CSV and CITS-CSV
make_gui(meta_in, cv.meta_validator.output_fp_json, '../results/meta_vis.html')
make_gui(cits_in, cv.cits_validator.output_fp_json, '../results/cits_vis.html')

# Merge the 2 HTML reports into a single, global one
merge_html_files('../results/meta_vis.html', '../results/cits_vis.html', '../results/global_vis.html')
"""