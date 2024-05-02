import csv
from bs4 import BeautifulSoup

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


def make_html_table(csv_path):

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, dialect='unix')

        for r in reader:
            colnames = r.keys()
            break

        row_no_col = '<th>row no.</th>'
        thead = f'<thead><tr>{row_no_col}{"".join([f"<th>{cn}</th>" for cn in colnames])}</tr></thead>'

        html_rows = []

        for row_idx, row in enumerate(reader):
            html_rows.append(make_html_row(row_idx, row))
        
        table:str = '<table>' + thead + "\n".join(html_rows) + '</table>'
    
    return table


def make_html_doc(html_table, out_html):
    with open(out_html, 'w', encoding='utf-8') as outf:
        full_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Table</title>
        </head>
        <body>
        {html_table}
        </body>
        </html>
        '''
        # soup = BeautifulSoup(full_content, 'html.parser')
        # pretty_doc = soup.prettify(formatter=custom_formatter)
        # outf.write(pretty_doc)
        outf.write(full_content)
    return full_content


if __name__ == '__main__':
    csv_path = './tmp/valid_meta.csv'

    table = make_html_table(csv_path)
    print(make_html_doc(table, 'tmp/html_doc_test.html'))
