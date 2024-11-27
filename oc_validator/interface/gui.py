import csv
import warnings
from bs4 import BeautifulSoup, Tag
from random import randint
from jinja2 import Environment, FileSystemLoader
from json import load
from os.path import realpath
from os.path import join, dirname, abspath
# from prettierfier import prettify_html
# import webbrowser


def make_html_row(row_idx, row):
    """
    Converts a single row from the CSV table into an HTML table row with custom appropriate structure.
    :param row_idx (int): the original index of the row to process, as it appears on the original table. Indexing is 1-based.
    :param row (dict): the dictionary representing the row
    :return (str): the HTML table row
    """

    html_string_list = []

    for col_name, value in row.items():
        cell_html_string = ''

        if value:
            new_value = value

            if col_name in ['id', 'citing_id', 'cited_id']:
                items = value.split()
                for idx, item in enumerate(items):
                    s = f'<span class="item"><span class="item-component">{item}</span></span>'
                    new_value = new_value.replace(item, s)
                new_value = f'<span class="field-value {col_name}">{new_value}</span>'

            elif col_name in ['author', 'editor', 'publisher']:
                items = value.split('; ')

                for idx, item in enumerate(items):
                    if '[' in item and ']' in item:
                        ids_start = item.index('[')+1
                        ids_end = item.index(']')
                        ids = item[ids_start:ids_end].split()
                        name = item[:ids_start-1].strip()
                        new_item = item

                        for id in ids:
                            new_item_component = f'<span class="item-component">{id}</span>'
                            new_item = new_item.replace(id, new_item_component)
                        new_item = new_item.replace(name, f'<span class="item-component">{name}</span>')
                        s = f'<span class="item">{new_item}</span>'
                        new_value = new_value.replace(item, s)
                    else:
                        s = f'<span class="item"><span class="item-component">{item}</span></span>'
                        new_value = new_value.replace(item, s)

                new_value = f'<span class="field-value {col_name}">{new_value}</span>'
                
            
            elif col_name == 'venue':
                if '[' in value and ']' in value:
                    ids_start = value.index('[')+1
                    ids_end = value.index(']')
                    ids = value[ids_start:ids_end].split()
                    name = value[:ids_start-1].strip()
                    new_item = value

                    for id in ids:
                        new_item_component = f'<span class="item-component">{id}</span>'
                        new_item = new_item.replace(id, new_item_component)
                    new_item = new_item.replace(name, f'<span class="item-component">{name}</span>')
                    new_value = f'<span class="field-value {col_name}"><span class="item">{new_item}</span></span>'

                else:
                    new_value = f'<span class="field-value {col_name}"><span class="item"><span class="item-component">{value}</span></span></span>'

            else: # i.e. if col_name in ['type', 'issue', 'volume', 'page', 'pub_date', 'citing_publication_date', 'cited_publication_date']:
                new_value = f'<span class="field-value {col_name}"><span class="item"><span class="item-component">{value}</span></span></span>'
            
            html_string_list.append(new_value)
        else:
            new_value = f'<span class="field-value {col_name}"><span class="item"><span class="item-component"></span></span></span>'
            html_string_list.append(new_value)

    row_no_cell = f'<td><span>{str(int(row_idx)+1)}</span></td>'
    # add row index both as a column in the table and as ID of the HTML element corresponding to the row
    res = f'<tr id="row{str(int(row_idx)+1)}">{row_no_cell}{"".join([f"<td>{cell_value}</td>" for cell_value in html_string_list])}</tr>'
    return res

def read_csv(csv_doc, del_position=0):
        delimiters_to_try=[',',';','\t']
        with open(csv_doc, 'r', encoding='utf-8') as f:
            data_dict = list(csv.DictReader(f, delimiter=delimiters_to_try[del_position]))
            if len(data_dict[0].keys()) > 1:  # if each dict has more than 1 key, it means it's read correctly
                return data_dict
            else:
                new_del_position = del_position+1
                return read_csv(csv_doc, new_del_position)  # try with another delimiter

def make_html_table(csv_path, rows_to_select: set, all_rows=False):
    """
    Converts the CSV table into an HTML table.
    :param csv_path: the file path to the CSV table data.
    :param rows_to_select (set): Set containing the indexes (integers) of the rows to be represented in the output HTML table. Row indexing is 1-based.
    :param all_rows: True if all the rows in the CSV table should be included in the output HTML table regardless of rows_to_select parameter, False otherwise. Defaults to False.
    :return (str): HTML string of the table (without validation information).
    """

    data = read_csv(csv_path)
    colnames = data[0].keys()

    row_no_col = '<th>row no.</th>'
    thead = f'<thead><tr>{row_no_col}{"".join([f"<th>{cn}</th>" for cn in colnames])}</tr></thead>'

    html_rows = []

    if not all_rows:
        for row_idx, row in enumerate(data):
            if row_idx in rows_to_select:
                html_rows.append(make_html_row(row_idx, row))

    else:  # all rows must be made html, ragardless of the content of rows_to_select
        if rows_to_select:
            warnings.warn('The output HTML table will include all the rows. To include only invalid rows, set all_rows to False.', UserWarning)
        for row_idx, row in enumerate(data):
            html_rows.append(make_html_row(row_idx, row))

    table:str = '<table id="table-data">' + thead + "\n".join(html_rows) + '</table>'

    return table


def add_err_info(htmldoc:str, json_filepath):
    """
    Adds validation information from the JSON validation report to the HTML table.
    :param htmldoc: the HTML table or the whole HTML document, as a string
    :param json_filepath: the filepath to the JSON validation report.
    :return: the HTML string enriched with validation information
    """

    with open(json_filepath, 'r', encoding='utf8') as jsonfile:
        report = load(jsonfile)
        data = BeautifulSoup(htmldoc, 'html.parser')

        for erridx, err in enumerate(report):
            color = "#{:06x}".format(randint(0, 0xFFFFFF))  # generates random hexadecimal color
            table = err['position']['table']
            for rowidx, fieldobj in table.items():
                htmlrow = data.find(id=f'row{str(int(rowidx)+1)}')
                for fieldkey, fieldvalue in fieldobj.items():
                    htmlfield = htmlrow.find(class_=fieldkey)
                    if fieldvalue is not None:
                        all_children_items = htmlfield.find_all(class_='item')
                        for itemidx in fieldvalue:
                            item: Tag = all_children_items[itemidx]
                            item['class'].append(f'err-idx-{erridx}')
                            item['class'].append('invalid-data')
                            item['class'].append('error') if err['error_type'] == 'error' else item['class'].append('warning')
                            square = data.new_tag('span', **{'class':'error'}) if err['error_type'] == 'error' else data.new_tag('span', **{'class':'warning'})# TODO: add if condition for warnings, assigning the class according to the error_type in the report
                            square['style'] = f'background-color: {color}'
                            square['class'].append('error-icon')
                            square['class'].append(f'err-idx-{erridx}')
                            square['title'] = err['message']
                            square['onclick'] = 'highlightInvolvedElements(this)'
                            item.insert_after(square)  # inserts span element representing the error metadata

                    else:
                        errorpart = htmlfield
                        errorpart['class'].append(f'err-idx-{erridx}')
                        errorpart['class'].append('invalid-data')
                        errorpart['class'].append('error') if err['error_type'] == 'error' else errorpart['class'].append('warning')
                        square = data.new_tag('span', **{'class':'error'}) if err['error_type'] == 'error' else data.new_tag('span', **{'class':'warning'})
                        square['style'] = f'background-color: {color}'
                        square['class'].append('error-icon')
                        square['class'].append(f'err-idx-{erridx}')
                        square['title'] = err['message']
                        square['onclick'] = 'highlightInvolvedElements(this)'
                        errorpart.insert_after(square)  # inserts span element representing the error metadata

        result = str(data)
        return result

def make_gui(csv_path, report_path, output_html_path):

    # Prepare the Jinja2 environment
    # env = Environment(loader=FileSystemLoader('.'))
    env = Environment(loader=FileSystemLoader(dirname(abspath(__file__))))

    with open(report_path, 'r', encoding='utf-8') as f:
        report:list = load(f)

    if not len(report):  # -> the table validates, no errors!
        print('The submitted data is valid and there are no errors to represent.')
        template = env.get_template('valid_template.html')
        html_output = template.render()
        with open(output_html_path, "w", encoding='utf-8') as file:
            file.write(html_output)
        html_doc_fp = file.name
        print(f"HTML document generated successfully at {realpath(html_doc_fp)}.")
        # webbrowser.open('file://' + realpath(html_doc_fp))  # automatically opens created html page on default browser
        return None

    error_count = len(report)

    # set Jinja template to the one for invalid data representation
    template = env.get_template('invalid-template.html')

    # get set containing the indexes of invalid rows
    invalid_rows = set()
    invalid_rows.update({int(idx) for d in report for idx in d['position']['table'].keys()})

    # create HTML table containing the invalid rows
    raw_html_table: str = make_html_table(csv_path, invalid_rows, all_rows=False)

    # add error information to the HTML table
    final_html_table = add_err_info(raw_html_table, report_path)

    # read CSS and JS files to integrate them into HTML document 
    with (
        open(join(dirname(abspath(__file__)), 'style.css'), 'r', encoding='utf-8') as cssf, 
        open(join(dirname(abspath(__file__)), 'script.js'), 'r', encoding='utf-8') as jsf
        ):
        stylesheet = cssf.read()
        script = jsf.read()

    # Render the template with the table
    html_output = template.render(
        table=final_html_table,
        error_count=error_count,
        stylesheet=stylesheet,
        script=script
        )

    # Save the resulting HTML document to a file
    with open(output_html_path, "w", encoding='utf-8') as file:
        file.write(html_output)
        html_doc_fp = file.name

    # webbrowser.open('file://' + realpath(html_doc_fp))  # Open the HTML file in the default web browser
    print(f"HTML document generated successfully at {realpath(html_doc_fp)}.")


def transpose_report(error_report:dict):
    """
    NOT USED!!!
    Reads the errorreport dictionary and creates a new dictionary where keys
    correspond to the indexes of the rows that are intereseted by an error,
    and values are the full objects representing those errors.
    """
    out_data = dict()
    for err_obj in error_report:
        rows = err_obj['position']['table'].keys()
        for row in rows:
            if row not in out_data:
                out_data[row] = [err_obj]
            else:
                out_data[row].append(err_obj)
    res = {int(key): value for key, value in sorted(out_data.items(), key=lambda item: int(item[0]))}

    return res


def merge_html_files(doc1_fp, doc2_fp, merged_out_fp):
    """
    Merges two HTML documents into a single document.
    """
    with open(doc1_fp, 'r', encoding='utf-8') as fhandle1, open(doc2_fp, 'r', encoding='utf-8') as fhandle2:
        soup1 = BeautifulSoup(fhandle1, 'html.parser')
        soup2 = BeautifulSoup(fhandle2, 'html.parser')

    # general_info_1 = soup1.find('div', class_='general-info')
    general_info_2 = soup2.find('div', class_='general-info')
    table_1_container = soup1.find('div', class_='table-container')
    table_2_container = soup2.find('div', class_='table-container')
    table_1_container.insert_after(general_info_2)
    general_info_2.insert_after(table_2_container)
    
    html_out = str(soup1)
    with open(merged_out_fp, "w", encoding='utf-8') as outf:
        outf.write(html_out)
    print(f"HTML document generated successfully at {realpath(outf.name)}.")