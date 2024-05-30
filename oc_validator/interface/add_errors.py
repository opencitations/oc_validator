from bs4 import BeautifulSoup, Tag
import json
from random import randint
from prettierfier import prettify_html

# in_html_filepath = 'html_doc_test.html'
# json_filepath = 'report.json'
# out_html_filepath = 'final_doc.html'


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
