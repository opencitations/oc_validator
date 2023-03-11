# Copyright (c) 2023, OpenCitations <contact@opencitations.net>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

from re import match, search, sub
from roman import fromRoman, InvalidRomanNumeralError
from oc_validator.helper import Helper


class Wellformedness:
    def __init__(self):
        self.descr = 'This class groups the function for validating the well-formedness of the document.'  # todo: remove descr?
        self.helper = Helper()

    def wellformedness_br_id(self, id_element):
        """
        Validates the well-formedness of a single element inside the 'citing_id', 'cited_id' or 'id' field of a row,
        checking its compliance with CITS-csv/META-CSV syntax.
        :param id_element: str
        :return: bool
        """
        id_pattern = r'^(doi|issn|isbn|pmid|pmcid|url|wikidata|wikipedia):\S+$'
        if match(id_pattern, id_element):
            return True
        else:
            return False

    def wellformedness_people_item(self, ra_item: str):
        """
        Validates the well-formedness of an item inside the 'author' or 'editor' field of a row,
        checking its compliance with META-CSV syntax.
        :param ra_item: str
        :return: bool
        """
        #  todo: create stricter regex for not allowing characters that are likely to be illegal in a person's name/surname
        #   (e.g. digits, apostrophe, underscore, full-stop, etc.)
        outside_brackets = r'(?:[^\s,;\[\]]+(?:\s[^\s,;\[\]]+)*),?(?:\s[^\s,;\[\]]+)*'
        inside_brackets = r'\[(crossref|orcid|viaf|wikidata|ror):\S+(?:\s(crossref|orcid|viaf|wikidata|ror):\S+)*\]'
        ra_item_pattern = f'^(?:({outside_brackets}\\s{inside_brackets})|({outside_brackets}\\s?)|({inside_brackets}))$'

        if match(ra_item_pattern, ra_item):
            return True
        else:
            return False

    def wellformedness_publisher_item(self, ra_item: str):
        """
        Validates the well-formedness of an item inside the 'publisher' field of a row,
        checking its compliance with META-CSV syntax.
        :param ra_item: str
        :return: bool
        """
        outside_brackets_pub = r'(?:[^\s\[\]]+(?:\s[^\s\[\]]+)*)'
        inside_brackets = r'\[(crossref|orcid|viaf|wikidata|ror):\S+(?:\s(crossref|orcid|viaf|wikidata|ror):\S+)*\]'
        ra_item_pattern = f'^(?:({outside_brackets_pub}\\s{inside_brackets})|({outside_brackets_pub}\\s?)|({inside_brackets}))$'

        if match(ra_item_pattern, ra_item):
            return True
        else:
            return False

    def orphan_ra_id(self, ra_item: str):
        """
        Looks for possible ID of responsible agents ('author', 'publisher' or 'editor') that are NOT enclosed in
        brackets, as they should be. Returns True if the input string is likely to contain one or more R.A. ID outside
        square brackets.
        :param ra_item: the item inside a R.A. field, as it is split by the '; ' separator.
        :return:
        bool, True if a match is found (the string is likely NOT well-formed), False if NO match is found.
        """
        if search(r'(crossref|orcid|viaf|wikidata|ror):', sub(r'\[.*\]', '', ra_item)):
            return True
        else:
            return False

    def wellformedness_date(self, date_field):
        """
        Validates the well-formedness of the content of the 'citing_publication_date', 'cited_publication_date'
        or 'pub_date' field of a row, checking its compliance with CITS-csv/META-CSV syntax.
        :param date_field: str
        :return: bool
        """
        date_pattern = r'^((?:\d{4}\-(?:0[1-9]|1[012])(?:\-(?:0[1-9]|[12][0-9]|3[01]))?)|(?:\d{4}))$'
        if match(date_pattern, date_field):
            return True
        else:
            return False

    def wellformedness_venue(self, venue_value: str):
        """
        Validates the well-formedness of the string inside the 'venue' field of a row,
        checking its compliance with META-CSV syntax.
        :param venue_value: str
        :return: bool
        """
        outside_brackets_venue = r'(?:[^\s\[\]]+(?:\s[^\s\[\]]+)*)'
        # pmcids are not valid identifiers for 'venues'!
        inside_brackets_venue = r'\[(doi|pmid|issn|isbn|url|wikidata|wikipedia):\S+(?:\s(doi|pmid|issn|isbn|url|wikidata|wikipedia):\S+)*\]'
        venue_pattern = f'^(?:({outside_brackets_venue}\\s{inside_brackets_venue})|({outside_brackets_venue}\\s?)|({inside_brackets_venue}))$'

        if match(venue_pattern, venue_value):
            return True
        else:
            return False

    def orphan_venue_id(self, venue_value: str):
        """
        Looks for IDs of BRs that might be a venue but are NOT enclosed in brackets, as they should be. Returns True if the
        input string is likely to contain one or more BR ID outside square brackets.
        :param venue_value: the value of the 'venue' field of a row.
        :return:
        bool, True if a match is found (the string is likely NOT well-formed), False if NO match is found.
        """
        if search(r'(doi|pmid|issn|isbn|url|wikidata|wikipedia):', sub(r'\[.*\]', '', venue_value)):
            return True
        else:
            return False

    def wellformedness_volume_issue(self, vi_value: str):
        """
        Validates the well-formedness of the string inside the 'volume' or 'issue' field of a row,
        checking its compliance with META-CSV syntax.
        :param vi_value: str
        :return: bool
        """
        vi_pattern = r'^\S+(?:\s\S+)*$'

        if match(vi_pattern, vi_value):
            return True
        else:
            return False

    def wellformedness_page(self, page_value: str):
        """
        Validates the well-formedness of the string inside the 'page' field of a row,
        checking its compliance with META-CSV syntax.
        :param page_value: str
        :return: bool
        """
        # todo: create stricter regex for roman numerals and valid intervals
        # NB: incorrect roman numerals and impossible ranges (e.g. 200-20) still validate!
        natural_number = r'([1-9][0-9]*)'
        roman_numeral = r'([IiVvXxLlCcDdMm]+)'
        single_alphanum = r'((?:(?:[A-Za-z]|[α-ωΑ-Ω])?[1-9]\d*)|(?:[1-9]\d*(?:[A-Za-z]|[α-ωΑ-Ω])?))'
        normal_page_pattern = f'^(?:{natural_number}|{roman_numeral})-(?:{natural_number}|{roman_numeral})$'
        alphanum_page_pattern = f'^{single_alphanum}-{single_alphanum}$'

        if match(normal_page_pattern, page_value):
            return True
        elif match(alphanum_page_pattern, page_value):
            return True
        else:
            return False

    def check_page_interval(self, page_interval: str):
        """
        Validates the interval expressed in the 'page' field, verifying that the start page is smaller than the end page.
        :param page_interval: the value of the 'page' field
        :return: True if the interval is valid OR if it is impossibile to convert it to an integer. False if the interval
            has been converted AND it is invalid, or if it does not need to be converted and it is invalid.
        """

        both_num = page_interval.split('-')
        converted = []
        for num_str in both_num:
            if num_str.isnumeric():
                converted.append(int(num_str))
            else:
                try:
                    converted.append(fromRoman(num_str.upper()))
                except InvalidRomanNumeralError:
                    return False

        if converted[0] < converted[1]:
            return True
        else:
            return False

    def wellformedness_type(self, type_value: str):
        """
        Validates the well-formedness of the string inside the 'type' field of a row,
        checking its compliance with META-CSV syntax.
        :param type_value: str
        :return: bool
        """
        valid_types = ['book', 'book chapter', 'book part', 'book section', 'book series', 'book set', 'book track',
                       'component', 'dataset', 'data file', 'dissertation', 'edited book', 'journal', 'journal article',
                       'journal issue', 'journal volume', 'monograph', 'other', 'peer review', 'posted content',
                       'web content', 'proceedings', 'proceedings article', 'proceedings series', 'reference book',
                       'reference entry', 'report', 'report series', 'series' 'standard', 'standard series']

        if type_value in valid_types:
            return True
        else:
            return False

    def get_missing_values(self, row: dict) -> dict:
        """
        Checks whether a row has all required fields, depending on the specified 'type' of the resource, in case the
        value of 'id' is not specified. If any required field value is missing, a dictionary for the row is created
        which includes both the field(s) conditioning the requirement and the field(s) that are missing: The field
        on which the requirement depends appear in the dictionary as <field name>:[0], while missing values appear as
        <field name>:None.
        :param row: (dict) a dict corresponding to a single row
        :return missing: (dict) the dictionary locating
        """

        # TODO: Consider using an external config file, as you do for checking id-type semantic alignment, since the list
        #  of accepted types might change/be extended frequently!

        missing = {}
        if not row['id']:  # ID value is missing

            if row['type']:  # ID is missing and 'type' is specified

                if row['type'] in ['book', 'dataset', 'data file', 'dissertation', 'edited book', 'journal',
                                   'journal article', 'monograph', 'other', 'peer review', 'posted content',
                                   'web content', 'proceedings article', 'reference book', 'report']:
                    if not row['title']:
                        missing['type'] = [0]
                        missing['title'] = None
                    if not row['pub_date']:
                        missing['type'] = [0]
                        missing['pub_date'] = None
                    if not row['author'] and not row['editor']:
                        missing['type'] = [0]
                        if not row['author']:
                            missing['author'] = None
                        if not row['editor']:
                            missing['editor'] = None

                elif row['type'] in ['book chapter', 'book part', 'book section', 'book track', 'component',
                                     'reference entry']:
                    if not row['title']:
                        missing['type'] = [0]
                        missing['title'] = None
                    if not row['venue']:
                        missing['type'] = [0]
                        missing['venue'] = None

                elif row['type'] in ['book series', 'book set', 'journal', 'proceedings', 'proceedings series',
                                     'report series', 'standard', 'standard series']:
                    if not row['title']:
                        missing['type'] = [0]
                        missing['title'] = None

                elif row['type'] == 'journal issue':
                    if not row['venue']:
                        missing['type'] = [0]
                        missing['venue'] = None
                    if not row['title'] and not row['issue']:
                        missing['type'] = [0]
                        if not row['title']:
                            missing['title'] = None
                        if not row['issue']:
                            missing['issue'] = None

                elif row['type'] == 'journal volume':
                    if not row['venue']:
                        missing['type'] = [0]
                        missing['venue'] = None
                    if not row['title'] and not row['volume']:
                        missing['type'] = [0]
                        if not row['title']:
                            missing['title'] = None
                        if not row['volume']:
                            missing['volume'] = None

            else:

                if not row['title']:
                    missing['type'] = None
                    missing['title'] = None
                if not row['pub_date']:
                    missing['type'] = None
                    missing['pub_date'] = None
                if not row['author'] and not row['editor']:
                    missing['type'] = None
                    if not row['author']:
                        missing['author'] = None
                    if not row['editor']:
                        missing['editor'] = None

        if row['id']:
            if row['volume']:
                if not row['venue']:
                    missing['volume'] = [0]
                    missing['venue'] = None
                if row['type'] not in ['journal article', 'journal volume', 'journal issue']:
                    missing['volume'] = [0]
                    if not row['type']:
                        missing['type'] = None
                    else:
                        missing['type'] = [0]

            if row['issue']:
                if not row['venue']:
                    missing['issue'] = [0]
                    missing['venue'] = None
                if row['type'] not in ['journal article', 'journal volume', 'journal issue']:
                    missing['issue'] = [0]
                    if not row['type']:
                        missing['type'] = None
                    else:
                        missing['type'] = [0]

        return missing

    def get_duplicates_cits(self, entities: list, data_dict: list, messages) -> list:
        """
        Creates a list of dictionaries containing the duplication error in the whole document, either within a row
        (self-citation) or between two or more rows (duplicate citations).
        :param entities: list containing sets of strings (the IDs), where each set corresponds to a bibliographic entity
        :param data_dict: the list of the document's rows, read as dictionaries
        :param messages: the dictionary containing the messages as they're read from the .yaml config file
        :return: list of dictionaries, each carrying full info about each duplication error within the document.
        """
        visited_dicts = []
        report = []
        for row_idx, row in enumerate(data_dict):
            citation = {'citing_id': '', 'cited_id': ''}

            citing_items = row['citing_id'].split(' ')
            for item in citing_items:
                if citation['citing_id'] == '':
                    for set_idx, set in enumerate(entities):
                        if item in set:  # mapping the single ID to its corresponding set representing the bibl. entity
                            citation['citing_id'] = set_idx
                            break

            cited_items = row['cited_id'].split(' ')
            for item in cited_items:
                if citation['cited_id'] == '':
                    for set_idx, set in enumerate(entities):
                        if item in set:  # mapping the single ID to its corresponding set representing the bibl. entity
                            citation['cited_id'] = set_idx
                            break

            # If a field contains only invalid items, it is not possible to map it to an entity set: process the row
            # only if both citing and cited are associated to an entity set, i.e. their value in the 'citation'
            # dictionary is not still an empty string (as it had been initialized).
            if citation['citing_id'] != '' and citation['cited_id'] != '':

                if citation['citing_id'] == citation['cited_id']:  # SELF-CITATION warning (an entity cites itself)
                    table = {
                        row_idx: {
                            'citing_id': [idx for idx in range(len(citing_items))],
                            'cited_id': [idx for idx in range(len(cited_items))]
                        }
                    }
                    message = messages['m4']
                    report.append(
                        self.helper.create_error_dict(validation_level='csv_wellformedness', error_type='warning',
                                                      message=message, error_label='self-citation', located_in='field',
                                                      table=table, valid=True))

                # SAVE CITATIONS BETWEEN ENTITIES IN A LIST.
                # Each citation is represented as a nested dictionary in which the key-values representing the entity-to-entity
                # citation are unique within the list, but the table representing the location of an INSTANCE of an
                # entity-to-entity citation is updated each time a new instance of such citation is found in the csv document.

                citation_table = {
                    row_idx: {
                        'citing_id': [idx for idx in range(len(citing_items))],
                        'cited_id': [idx for idx in range(len(cited_items))]
                    }
                }

                cit_info = {'citation': citation, 'table': citation_table}

                if not visited_dicts:  # just for the first round of the iteration (when visited_dicts is empty)
                    visited_dicts.append(cit_info)
                else:
                    for dict_idx, cit_dict in enumerate(visited_dicts):
                        if citation == cit_dict['citation']:
                            visited_dicts[dict_idx]['table'].update(cit_info['table'])
                            break
                        elif dict_idx == (len(visited_dicts) - 1):
                            visited_dicts.append(cit_info)

        for d in visited_dicts:
            if len(d['table']) > 1:  # if there's more than 1 row in table for a citation (duplicate rows error)
                table = d['table']
                message = messages['m5']

                report.append(
                    self.helper.create_error_dict(validation_level='csv_wellformedness', error_type='error',
                                                  message=message, error_label='duplicate_citation', located_in='row',
                                                  table=table))
        return report

    def get_duplicates_meta(self, entities: list, data_dict: list, messages) -> list:
        """
        Creates a list of dictionaries containing the duplication error in the whole document between two or more rows.
        :param entities: list containing sets of strings (the IDs), where each set corresponds to a bibliographic entity.
        :param data_dict: the list of the document's rows, read as dictionaries
        :param messages: the dictionary containing the messages as they're read from the .yaml config file
        :return: list of dictionaries, each carrying full info about each duplication error within the document.
        """
        visited_dicts = []
        report = []
        for row_idx, row in enumerate(data_dict):
            br = {'meta_id': None, 'table': {}}
            items = row['id'].split(' ')

            for item in items:
                if not br['meta_id']:
                    for set_idx, set in enumerate(entities):
                        if item in set:  # mapping the single ID to its corresponding set representing the bibl. entity
                            br['meta_id'] = str(set_idx)
                            br['table'] = {row_idx: {'id': list(range(len(items)))}}
                            break

            # process row only if a meta_id has been associated to it (i.e. id field contains at least one valid identifier)
            if br['meta_id']:
                if not visited_dicts:  # just for the first round of the iteration (when visited_dicts is empty)
                    visited_dicts.append(br)
                else:
                    for visited_br_idx, visited_br in enumerate(visited_dicts):
                        if br['meta_id'] == visited_br['meta_id']:
                            visited_dicts[visited_br_idx]['table'].update(br['table'])
                            break
                        elif visited_br_idx == (len(visited_dicts) - 1):
                            visited_dicts.append(br)

        for d in visited_dicts:
            if len(d['table']) > 1:  # if there's more than 1 row in table for a br (duplicate rows error)
                table = d['table']
                message = messages['m11']

                report.append(
                    self.helper.create_error_dict(validation_level='csv_wellformedness', error_type='error',
                                                  message=message, error_label='duplicate_br', located_in='row',
                                                  table=table))

        return report
