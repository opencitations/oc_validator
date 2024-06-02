import csv
import json
import warnings
from bs4 import BeautifulSoup, Tag
from random import randint
from prettierfier import prettify_html


def make_html_row(row_idx, row):

    html_string_list = []

    for col_name, value in row.items():
        cell_html_string = ''

        if value:
            new_value = value

            if col_name == 'id':
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

            else: # i.e. if col_name in ['type', 'issue', 'volume', 'page', 'pub_date']:
                new_value = f'<span class="field-value {col_name}"><span class="item"><span class="item-component">{value}</span></span></span>'
            
            html_string_list.append(new_value)
            #print(new_value, '\n')
        else:
            new_value = f'<span class="field-value {col_name}"><span class="item"><span class="item-component"></span></span></span>'
            html_string_list.append(new_value)

    row_no_cell = f'<td><span>{row_idx}</span></td>'
    # add row index both as a column in the table and as ID of the HTML element corresponding to the row
    res = f'<tr id="row{row_idx}">{row_no_cell}{"".join([f"<td>{cell_value}</td>" for cell_value in html_string_list])}</tr>'
    return res


def make_html_table(csv_path, rows_to_select: set, all_rows=False):

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, dialect='unix')
        colnames = reader.fieldnames

        row_no_col = '<th>row no.</th>'
        thead = f'<thead><tr>{row_no_col}{"".join([f"<th>{cn}</th>" for cn in colnames])}</tr></thead>'

        html_rows = []

        if not all_rows:
            for row_idx, row in enumerate(reader):
                if row_idx in rows_to_select:
                    html_rows.append(make_html_row(row_idx, row))

        else:  # all rows must be made html, ragardless of the content of rows_to_select
            if rows_to_select:
                warnings.warn('The output HTML table will include all the rows. To include only invalid rows, set all_rows to False.', UserWarning)
            for row_idx, row in enumerate(reader):
                html_rows.append(make_html_row(row_idx, row))

        table:str = '<table id="table-data">' + thead + "\n".join(html_rows) + '</table>'
        # table:str = '<table id="table-data">' + thead + "".join(html_rows) + '</table>'

    return table


def add_err_info(htmldoc:str, json_filepath):

    with open(json_filepath, 'r', encoding='utf8') as jsonfile:
        report = json.load(jsonfile)
        data = BeautifulSoup(htmldoc, 'html.parser')

        for erridx, err in enumerate(report):
            color = "#{:06x}".format(randint(0, 0xFFFFFF))  # generates random hexadecimal color
            table = err['position']['table']
            for rowidx, fieldobj in table.items():
                htmlrow = data.find(id=f'row{rowidx}')
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


def transpose_report(error_report:dict):
    """
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


def select_elements(jsonreport):
    with open(jsonreport, 'r', encoding='utf-8') as jsonfile:
        data:list = json.load(jsonfile)
        for idx, obj in enumerate(data):
            selectors = []
            objectid = f'err{idx}'
            located_in = obj['located_in']

            involved_elements_position = obj['position']['table']

            for row_idx, field in involved_elements_position.items():
                for field_name, itemlist in field.items():
                    for itemidx in itemlist:
                        selector = f'`#row${row_idx + 1} .field-value.${field_name} .item:nth-child(${itemidx + 1})`'
                        selectors.append(selector)
            yield selectors

