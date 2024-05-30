from jinja2 import Environment, FileSystemLoader
from oc_validator.interface.gui import make_html_table
from add_errors import add_err_info
from prettierfier import prettify_html
from json import load

# Load the Jinja2 template
env = Environment(loader=FileSystemLoader('.'))
template = env.get_template('template.html')


csv_path = 'invalid_meta.csv'
report_path = 'sample_report.json'

# get set containing the indexes of invalid rows
with open(report_path, 'r', encoding='utf-8') as f:
    report = load(f)
invalid_rows = set()
invalid_rows.update({int(idx) for d in report for idx in d['position']['table'].keys()})

# create HTML table containing the invalid rows
raw_html_table: str = make_html_table(csv_path, invalid_rows, all_rows=False)

# add error information to the HTML table
final_html_table = add_err_info(raw_html_table, report_path)


# Render the template with the table
html_output = template.render(table=final_html_table)

# Save the resulting HTML document to a file
with open("example.html", "w", encoding='utf-8') as file:
    file.write(html_output)

print("HTML document generated successfully.")
