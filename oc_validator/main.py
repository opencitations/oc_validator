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

from csv import DictReader
from yaml import full_load
from json import load, dump
from os.path import exists, join, dirname, abspath
from os import makedirs, getcwd
from re import finditer
from oc_validator.helper import Helper
from oc_validator.csv_wellformedness import Wellformedness
from oc_validator.id_syntax import IdSyntax
from oc_validator.id_existence import IdExistence
from oc_validator.semantics import Semantics
from tqdm import tqdm
from argparse import ArgumentParser


# --- Custom Exception classes. ---
class ValidationError(Exception):
    """Base class for errors related to the validation process."""
    pass

class InvalidTableError(ValidationError):
    """Raised when the submitted table cannot be identified as META-CSV or CITS-CSV, therefore cannot be processed."""
    def __init__(self, input_fp):
        super().__init__('The submitted table does not meet the required basic formatting standards. '
                         'Please ensure that both the metadata and citations tables are valid CSV files following the correct structure: '
                         'the metadata table must have the following columns: "id", "title", "author", "pub_date", "venue", "volume", "issue", "page", "type", "publisher", "editor"; '
                         'the citations table must have either 4 columns ("citing_id", "citing_publication_date", "cited_id", "cited_publication_date") or two columns ("citing_id","cited_id")'
                         'Refer to the documentation at https://github.com/opencitations/crowdsourcing/blob/main/README.md for the expected format and structure before resubmitting your deposit.')
        self.input_fp = input_fp

class TableNotMatchingInstance(ValidationError):
    """Raised when the table submitted for a specific Validator instance in ClosureValidator does not match the process validation type,
        e.g. a CITS-CSV table is submitted for an instance of Validator that is intended to process a META-CSV table.
    """
    def __init__(self, input_fp, detected_table_type, correct_table_type):
        super().__init__(f'The submitted table in file "{input_fp}" is of type {detected_table_type}, but should be of type {correct_table_type} instead.')
        self.input_fp = input_fp
        self.detected_table_type = detected_table_type
        self.correct_table_type = correct_table_type

# --- Class for the main process; validates one document at a time via the Validator.validate() method. ---
class Validator:
    def __init__(self, csv_doc: str, output_dir: str, use_meta_endpoint=False, verify_id_existence=True):
        self.csv_doc = csv_doc
        self.data = self.read_csv(self.csv_doc)
        self.table_to_process = self.process_selector(self.data)
        self.helper = Helper()
        self.wellformed = Wellformedness()
        self.syntax = IdSyntax()
        self.existence = IdExistence(use_meta_endpoint=use_meta_endpoint)
        self.semantics = Semantics()
        script_dir = dirname(abspath(__file__))  # Directory where the script is located
        self.messages = full_load(open(join(script_dir, 'messages.yaml'), 'r', encoding='utf-8'))
        self.id_type_dict = load(open(join(script_dir, 'id_type_alignment.json'), 'r', encoding='utf-8'))
        self.output_dir = output_dir
        if not exists(self.output_dir):
            makedirs(self.output_dir)
        if self.table_to_process == 'meta_csv':
            self.output_fp_json = self._make_output_filepath('out_validate_meta', 'json')
            self.output_fp_txt = self._make_output_filepath('meta_validation_summary', 'txt')
        elif self.table_to_process == 'cits_csv':
            self.output_fp_json = self._make_output_filepath('out_validate_cits', 'json')
            self.output_fp_txt = self._make_output_filepath('cits_validation_summary', 'txt')
        self.visited_ids = dict()
        self.verify_id_existence = verify_id_existence

    def read_csv(self, csv_doc, del_position=0):
        delimiters_to_try=[',',';','\t']
        with open(csv_doc, 'r', encoding='utf-8') as f:
            data_dict = list(DictReader(f, delimiter=delimiters_to_try[del_position]))
            if len(data_dict[0].keys()) > 1:  # if each dict has more than 1 key, it means it's read correctly
                return data_dict
            else:
                new_del_position = del_position+1
                return self.read_csv(csv_doc, new_del_position)  # try with another delimiter

    def process_selector(self, data: list):
        process_type = None
        try:
            if all(set(row.keys()) == {"id", "title", "author", "pub_date", "venue", "volume", "issue", "page", "type",
                                        "publisher", "editor"} for row in data):
                process_type = 'meta_csv'
                return process_type
            elif all(set(row.keys()) == {'citing_id', 'citing_publication_date', 'cited_id', 'cited_publication_date'} for row in data):
                process_type = 'cits_csv'
                return process_type
            elif all(set(row.keys()) == {'citing_id', 'cited_id'} for row in data): # support also Index tables with no publication dates
                process_type = 'cits_csv'
                return process_type
            else:
                raise InvalidTableError(self.csv_doc)
        except KeyError:
            raise InvalidTableError(self.csv_doc)
        
    def _make_output_filepath(self, base_filename, extension):
        """
        Generates a unique output filepath, checks if a file with the same name exists, and if so appends an incrementing number.
        """
        
        full_path = join(self.output_dir, f"{base_filename}.{extension}")
        counter = 1

        # If filepath already exists, increment the counter and check for existing files
        while exists(full_path):
            full_path = join(self.output_dir, f"{base_filename}_{counter}.{extension}")
            counter += 1
        
        return full_path

    def validate(self):
        if self.table_to_process == 'meta_csv':
            return self.validate_meta()
        elif self.table_to_process == 'cits_csv':
            return self.validate_cits()

    def validate_meta(self) -> list:
        """
        Validate an instance of META-CSV
        :return: the list of errors, i.e. the report of the validation process
        """
        error_final_report = []

        messages = self.messages
        id_type_dict = self.id_type_dict

        br_id_groups = []

        for row_idx, row in enumerate(tqdm(self.data)):
            row_ok = True  # switch for row well-formedness
            id_ok = True  # switch for id field well-formedness
            type_ok = True  # switch for type field well-formedness

            missing_required_fields = self.wellformed.get_missing_values(
                row)  # dict w/ positions of error in row; empty if row is fine
            if missing_required_fields:
                message = messages['m17']
                table = {row_idx: missing_required_fields}
                error_final_report.append(
                    self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                  error_type='error',
                                                  message=message,
                                                  error_label='required_fields',
                                                  located_in='field',
                                                  table=table))
                row_ok = False

            for field, value in row.items():

                if field == 'id':
                    if value:
                        br_ids_set = set()  # set where to put well-formed br IDs only
                        items = value.split(' ')

                        for item_idx, item in enumerate(items):

                            if item == '':
                                message = messages['m1']
                                table = {row_idx: {field: [item_idx]}}
                                error_final_report.append(
                                    self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                  error_type='error',
                                                                  message=message,
                                                                  error_label='extra_space',
                                                                  located_in='item',
                                                                  table=table))

                            elif not self.wellformed.wellformedness_br_id(item):
                                message = messages['m2']
                                table = {row_idx: {field: [item_idx]}}
                                error_final_report.append(
                                    self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                  error_type='error',
                                                                  message=message,
                                                                  error_label='br_id_format',
                                                                  located_in='item',
                                                                  table=table))

                            else:
                                if item not in br_ids_set:
                                    br_ids_set.add(item)
                                else:  # in-field duplication of the same ID
                                    table = {row_idx: {field: [i for i, v in enumerate(items) if v == item]}}
                                    message = messages['m6']

                                    error_final_report.append(
                                        self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                      error_type='error',
                                                                      message=message,
                                                                      error_label='duplicate_id',
                                                                      located_in='item',
                                                                      table=table)  # valid=False
                                    )

                                #  2nd validation level: EXTERNAL SYNTAX OF ID (BIBLIOGRAPHIC RESOURCE)
                                if not self.syntax.check_id_syntax(item):
                                    message = messages['m19']
                                    table = {row_idx: {field: [item_idx]}}
                                    error_final_report.append(
                                        self.helper.create_error_dict(validation_level='external_syntax',
                                                                      error_type='error',
                                                                      message=message,
                                                                      error_label='br_id_syntax',
                                                                      located_in='item',
                                                                      table=table))
                                #  3rd validation level: EXISTENCE OF ID (BIBLIOGRAPHIC RESOURCE)
                                else:
                                    if self.verify_id_existence: # if verify_id_existence is False just skip these operations
                                        message = messages['m20']
                                        table = {row_idx: {field: [item_idx]}}
                                        if item not in self.visited_ids:
                                            if not self.existence.check_id_existence(item):
                                                error_final_report.append(
                                                    self.helper.create_error_dict(validation_level='existence',
                                                                                error_type='warning',
                                                                                message=message,
                                                                                error_label='br_id_existence',
                                                                                located_in='item',
                                                                                table=table, valid=True))
                                                self.visited_ids[item] = False
                                            else:
                                                self.visited_ids[item] = True
                                        elif self.visited_ids[item] is False:
                                            error_final_report.append(
                                                self.helper.create_error_dict(validation_level='existence',
                                                                            error_type='warning',
                                                                            message=message,
                                                                            error_label='br_id_existence',
                                                                            located_in='item',
                                                                            table=table, valid=True))

                        if len(br_ids_set) >= 1:
                            br_id_groups.append(br_ids_set)

                        if len(br_ids_set) != len(items):  # --> some well-formedness error occurred in the id field
                            id_ok = False

                if field == 'title':
                    if value:
                        if value.isupper():
                            message = messages['m8']
                            table = {row_idx: {field: [0]}}
                            error_final_report.append(
                                self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                              error_type='warning',
                                                              message=message,
                                                              error_label='uppercase_title',
                                                              located_in='item',
                                                              table=table,
                                                              valid=True))

                if field == 'author' or field == 'editor':
                    if value:
                        items = value.split('; ')

                        for item_idx, item in enumerate(items):

                            if self.wellformed.orphan_ra_id(item):
                                message = messages['m10']
                                table = {row_idx: {field: [item_idx]}}
                                error_final_report.append(
                                    self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                  error_type='warning',
                                                                  message=message,
                                                                  error_label='orphan_ra_id',
                                                                  located_in='item',
                                                                  table=table,
                                                                  valid=True))

                            if not self.wellformed.wellformedness_people_item(item):
                                message = messages['m9']
                                table = {row_idx: {field: [item_idx]}}
                                error_final_report.append(
                                    self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                  error_type='error',
                                                                  message=message,
                                                                  error_label='people_item_format',
                                                                  located_in='item',
                                                                  table=table))

                            else:
                                ids = [m.group() for m in
                                       finditer(r'((?:crossref|orcid|viaf|wikidata|ror):\S+)(?=\s|\])', item)]

                                for id in ids:
                                    #  2nd validation level: EXTERNAL SYNTAX OF ID (RESPONSIBLE AGENT)
                                    if not self.syntax.check_id_syntax(id):
                                        message = messages['m21']
                                        table = {row_idx: {field: [item_idx]}}
                                        error_final_report.append(
                                            self.helper.create_error_dict(validation_level='external_syntax',
                                                                          error_type='error',
                                                                          message=message,
                                                                          error_label='ra_id_syntax',
                                                                          located_in='item',
                                                                          table=table))
                                    #  3rd validation level: EXISTENCE OF ID (RESPONSIBLE AGENT)
                                    else:
                                        if self.verify_id_existence: # if verify_id_existence is False just skip these operations
                                            message = messages['m22']
                                            table = {row_idx: {field: [item_idx]}}
                                            if id not in self.visited_ids:
                                                if not self.existence.check_id_existence(id):
                                                    error_final_report.append(
                                                        self.helper.create_error_dict(validation_level='existence',
                                                                                    error_type='warning',
                                                                                    message=message,
                                                                                    error_label='ra_id_existence',
                                                                                    located_in='item',
                                                                                    table=table,
                                                                                    valid=True))
                                                    self.visited_ids[id] = False
                                                else:
                                                    self.visited_ids[id] = True
                                            elif self.visited_ids[id] is False:
                                                error_final_report.append(
                                                    self.helper.create_error_dict(validation_level='existence',
                                                                                error_type='warning',
                                                                                message=message,
                                                                                error_label='ra_id_existence',
                                                                                located_in='item',
                                                                                table=table,
                                                                                valid=True))
                if field == 'pub_date':
                    if value:
                        if not self.wellformed.wellformedness_date(value):
                            message = messages['m3']
                            table = {row_idx: {field: [0]}}
                            error_final_report.append(
                                self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                              error_type='error',
                                                              message=message,
                                                              error_label='date_format',
                                                              located_in='item',
                                                              table=table))

                if field == 'venue':
                    if value:

                        if self.wellformed.orphan_venue_id(value):
                            message = messages['m15']
                            table = {row_idx: {field: [0]}}
                            error_final_report.append(
                                self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                              error_type='warning',
                                                              message=message,
                                                              error_label='orphan_venue_id',
                                                              located_in='item',
                                                              table=table,
                                                              valid=True))

                        if not self.wellformed.wellformedness_venue(value):
                            message = messages['m12']
                            table = {row_idx: {field: [0]}}
                            error_final_report.append(
                                self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                              error_type='error',
                                                              message=message,
                                                              error_label='venue_format',
                                                              located_in='item',
                                                              table=table))

                        else:
                            ids = [m.group() for m in
                                   finditer(r'((?:doi|issn|isbn|url|wikidata|wikipedia|openalex):\S+)(?=\s|\])', value)] # local: and temp: IDs should not be in venue

                            for id in ids:

                                #  2nd validation level: EXTERNAL SYNTAX OF ID (BIBLIOGRAPHIC RESOURCE)
                                if not self.syntax.check_id_syntax(id):
                                    message = messages['m19']
                                    table = {row_idx: {field: [0]}}
                                    error_final_report.append(
                                        self.helper.create_error_dict(validation_level='external_syntax',
                                                                      error_type='error',
                                                                      message=message,
                                                                      error_label='br_id_syntax',
                                                                      located_in='item',
                                                                      table=table))
                                #  3rd validation level: EXISTENCE OF ID (BIBLIOGRAPHIC RESOURCE)
                                else:
                                    if self.verify_id_existence: # if verify_id_existence is False just skip these operations
                                        message = messages['m20']
                                        table = {row_idx: {field: [0]}}
                                        if id not in self.visited_ids:
                                            if not self.existence.check_id_existence(id):
                                                error_final_report.append(
                                                    self.helper.create_error_dict(validation_level='existence',
                                                                                error_type='warning',
                                                                                message=message,
                                                                                error_label='br_id_existence',
                                                                                located_in='item',
                                                                                table=table,
                                                                                valid=True))
                                                self.visited_ids[id] = False
                                            else:
                                                self.visited_ids[id] = True
                                        elif self.visited_ids[id] is False:
                                            error_final_report.append(
                                                self.helper.create_error_dict(validation_level='existence',
                                                                            error_type='warning',
                                                                            message=message,
                                                                            error_label='br_id_existence',
                                                                            located_in='item',
                                                                            table=table,
                                                                            valid=True))

                if field == 'volume':
                    if value:
                        if not self.wellformed.wellformedness_volume_issue(value):
                            message = messages['m13']
                            table = {row_idx: {field: [0]}}
                            error_final_report.append(
                                self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                              error_type='error',
                                                              message=message,
                                                              error_label='volume_issue_format',
                                                              located_in='item',
                                                              table=table))

                if field == 'issue':
                    if value:
                        if not self.wellformed.wellformedness_volume_issue(value):
                            message = messages['m13']
                            table = {row_idx: {field: [0]}}
                            error_final_report.append(
                                self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                              error_type='error',
                                                              message=message,
                                                              error_label='volume_issue_format',
                                                              located_in='item',
                                                              table=table))

                if field == 'page':
                    if value:
                        if not self.wellformed.wellformedness_page(value):
                            message = messages['m14']
                            table = {row_idx: {field: [0]}}
                            error_final_report.append(
                                self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                              error_type='error',
                                                              message=message,
                                                              error_label='page_format',
                                                              located_in='item',
                                                              table=table))
                        else:
                            if not self.wellformed.check_page_interval(value):
                                message = messages['m18']
                                table = {row_idx: {field: [0]}}
                                error_final_report.append(
                                    self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                  error_type='warning',
                                                                  message=message,
                                                                  error_label='page_interval',
                                                                  located_in='item',
                                                                  table=table,
                                                                  valid=True))

                if field == 'type':
                    if value:
                        if not self.wellformed.wellformedness_type(value):
                            message = messages['m16']
                            table = {row_idx: {field: [0]}}
                            error_final_report.append(
                                self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                              error_type='error',
                                                              message=message,
                                                              error_label='type_format',
                                                              located_in='item',
                                                              table=table))

                            type_ok = False

                if field == 'publisher':
                    if value:
                        items = value.split('; ')
                        for item_idx, item in enumerate(items):
                            if self.wellformed.orphan_ra_id(value):
                                message = messages['m10']
                                table = {row_idx: {field: [item_idx]}}
                                error_final_report.append(
                                    self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                  error_type='warning',
                                                                  message=message,
                                                                  error_label='orphan_ra_id',
                                                                  located_in='item',
                                                                  table=table,
                                                                  valid=True))

                            if not self.wellformed.wellformedness_publisher_item(value):
                                message = messages['m9']
                                table = {row_idx: {field: [item_idx]}}
                                error_final_report.append(
                                    self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                  error_type='error',
                                                                  message=message,
                                                                  error_label='publisher_format',
                                                                  located_in='item',
                                                                  table=table))

                            else:
                                ids = [m.group() for m in
                                       finditer(r'((?:crossref|orcid|viaf|wikidata|ror):\S+)(?=\s|\])', value)]

                                for id in ids:

                                    #  2nd validation level: EXTERNAL SYNTAX OF ID (RESPONSIBLE AGENT)
                                    if not self.syntax.check_id_syntax(id):
                                        message = messages['m21']
                                        table = {row_idx: {field: [item_idx]}}
                                        error_final_report.append(
                                            self.helper.create_error_dict(validation_level='external_syntax',
                                                                          error_type='error',
                                                                          message=message,
                                                                          error_label='ra_id_syntax',
                                                                          located_in='item',
                                                                          table=table))
                                    #  3rd validation level: EXISTENCE OF ID (RESPONSIBLE AGENT)
                                    else:
                                        if self.verify_id_existence: # if verify_id_existence is False just skip these operations
                                            message = messages['m22']
                                            table = {row_idx: {field: [item_idx]}}
                                            if id not in self.visited_ids:
                                                if not self.existence.check_id_existence(id):
                                                    error_final_report.append(
                                                        self.helper.create_error_dict(validation_level='existence',
                                                                                    error_type='warning',
                                                                                    message=message,
                                                                                    error_label='ra_id_existence',
                                                                                    located_in='item',
                                                                                    table=table,
                                                                                    valid=True))
                                                    self.visited_ids[id] = False
                                                else:
                                                    self.visited_ids[id] = True
                                            elif self.visited_ids[id] is False:
                                                error_final_report.append(
                                                    self.helper.create_error_dict(validation_level='existence',
                                                                                error_type='warning',
                                                                                message=message,
                                                                                error_label='ra_id_existence',
                                                                                located_in='item',
                                                                                table=table,
                                                                                valid=True))

            if row_ok and id_ok and type_ok:  # row semantics is checked only when the involved parts are well-formed

                invalid_semantics = self.semantics.check_semantics(row, id_type_dict)
                if invalid_semantics:
                    message = messages['m23']
                    table = {row_idx: invalid_semantics}
                    error_final_report.append(
                        self.helper.create_error_dict(validation_level='semantics',
                                                      error_type='error',
                                                      message=message,
                                                      error_label='row_semantics',
                                                      located_in='field',
                                                      table=table))

        # GET BIBLIOGRAPHIC ENTITIES
        br_entities = self.helper.group_ids(br_id_groups)

        # GET DUPLICATE BIBLIOGRAPHIC ENTITIES (returns the list of error reports)
        duplicate_report = self.wellformed.get_duplicates_meta(entities=br_entities, data_dict=self.data,
                                                               messages=messages)

        if duplicate_report:
            error_final_report.extend(duplicate_report)

        # write error_final_report to external JSON file
        with open(self.output_fp_json, 'w', encoding='utf-8') as f:
            dump(error_final_report, f, indent=4)

        # write human-readable validation summary to txt file
        textual_report = self.helper.create_validation_summary(error_final_report)
        with open(self.output_fp_txt, "w", encoding='utf-8') as f:
            f.write(textual_report)

        return error_final_report

    def validate_cits(self) -> list:
        """
        Validates an instance of CITS-CSV.
        :return: the list of errors, i.e. the report of the validation process
        """

        error_final_report = []

        messages = self.messages

        id_fields_instances = []

        for row_idx, row in enumerate(tqdm(self.data)):
            for field, value in row.items():
                if field == 'citing_id' or field == 'cited_id':
                    if not value:  # Check required fields
                        message = messages['m7']
                        table = {row_idx: {field: None}}
                        error_final_report.append(
                            self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                          error_type='error',
                                                          message=message,
                                                          error_label='required_value_cits',
                                                          located_in='field',
                                                          table=table))
                    else:  # i.e. if string is not empty...
                        ids_set = set()  # set where to put valid IDs only
                        items = value.split(' ')

                        for item_idx, item in enumerate(items):

                            if item == '':
                                message = messages['m1']
                                table = {row_idx: {field: [item_idx]}}
                                error_final_report.append(
                                    self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                  error_type='error',
                                                                  message=message,
                                                                  error_label='extra_space',
                                                                  located_in='item',
                                                                  table=table))

                            elif not self.wellformed.wellformedness_br_id(item):
                                message = messages['m2']
                                table = {row_idx: {field: [item_idx]}}
                                error_final_report.append(
                                    self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                  error_type='error',
                                                                  message=message,
                                                                  error_label='br_id_format',
                                                                  located_in='item',
                                                                  table=table))

                            else:
                                if item not in ids_set:
                                    ids_set.add(item)
                                else:  # in-field duplication of the same ID

                                    table = {row_idx: {field: [i for i, v in enumerate(items) if v == item]}}
                                    message = messages['m6']

                                    error_final_report.append(
                                        self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                                      error_type='error',
                                                                      message=message,
                                                                      error_label='duplicate_id',
                                                                      located_in='item',
                                                                      table=table)  # 'valid'=False
                                    )
                                #  2nd validation level: EXTERNAL SYNTAX OF ID (BIBLIOGRAPHIC RESOURCE)
                                if not self.syntax.check_id_syntax(item):
                                    message = messages['m19']
                                    table = {row_idx: {field: [item_idx]}}
                                    error_final_report.append(
                                        self.helper.create_error_dict(validation_level='external_syntax',
                                                                      error_type='error',
                                                                      message=message,
                                                                      error_label='br_id_syntax',
                                                                      located_in='item',
                                                                      table=table))
                                #  3rd validation level: EXISTENCE OF ID (BIBLIOGRAPHIC RESOURCE)
                                else:
                                    if self.verify_id_existence: # if verify_id_existence is False just skip these operations
                                        message = messages['m20']
                                        table = {row_idx: {field: [item_idx]}}
                                        if item not in self.visited_ids:
                                            if not self.existence.check_id_existence(item):
                                                error_final_report.append(
                                                    self.helper.create_error_dict(validation_level='existence',
                                                                                error_type='warning',
                                                                                message=message,
                                                                                error_label='br_id_existence',
                                                                                located_in='item',
                                                                                table=table, valid=True))
                                                self.visited_ids[item] = False
                                            else:
                                                self.visited_ids[item] = True
                                        elif self.visited_ids[item] is False:
                                            error_final_report.append(
                                                self.helper.create_error_dict(validation_level='existence',
                                                                            error_type='warning',
                                                                            message=message,
                                                                            error_label='br_id_existence',
                                                                            located_in='item',
                                                                            table=table, valid=True))

                        if len(ids_set) >= 1:
                            id_fields_instances.append(ids_set)

                if field == 'citing_publication_date' or field == 'cited_publication_date':
                    if value:
                        if not self.wellformed.wellformedness_date(value):
                            message = messages['m3']
                            table = {row_idx: {field: [0]}}
                            error_final_report.append(
                                self.helper.create_error_dict(validation_level='csv_wellformedness',
                                                              error_type='error',
                                                              message=message,
                                                              error_label='date_format',
                                                              located_in='item',
                                                              table=table))

        # GET BIBLIOGRAPHIC ENTITIES
        entities = self.helper.group_ids(id_fields_instances)
        # GET SELF-CITATIONS AND DUPLICATE CITATIONS (returns the list of error reports)
        duplicate_report = self.wellformed.get_duplicates_cits(entities=entities,
                                                               data_dict=self.data,
                                                               messages=messages)
        if duplicate_report:
            error_final_report.extend(duplicate_report)

        # write error_final_report to external JSON file
        with open(self.output_fp_json, 'w', encoding='utf-8') as f:
            dump(error_final_report, f, indent=4)

        # write human-readable validation summary to txt file
        textual_report = self.helper.create_validation_summary(error_final_report)
        with open(self.output_fp_txt, "w", encoding='utf-8') as f:
            f.write(textual_report)

        return error_final_report


class ClosureValidator:

    def __init__(self, meta_csv_doc, meta_output_dir, cits_csv_doc, cits_output_dir, strict_sequenciality=False, meta_kwargs=None, cits_kwargs=None) -> None:
        self.meta_csv_doc = meta_csv_doc
        self.meta_output_dir = meta_output_dir
        self.cits_csv_doc = cits_csv_doc
        self.cits_output_dir = cits_output_dir
        self.strict_sequentiality = strict_sequenciality  # if True, runs the check on transitive closure if and only if the other checks passed without errors

        script_dir = dirname(abspath(__file__))  # Directory where the script is located
        self.messages = full_load(open(join(script_dir, 'messages.yaml'), 'r', encoding='utf-8'))

        # Define default kwargs for optional configuration of the two instances of Validator
        default_kwargs = {'use_meta_endpoint': False, 'verify_id_existence': True}

        # Merge user-provided kwargs with defaults
        meta_kwargs = {**default_kwargs, **(meta_kwargs or {})}
        cits_kwargs = {**default_kwargs, **(cits_kwargs or {})}

        # Create Validator instances with merged kwargs
        self.meta_validator = Validator(self.meta_csv_doc, self.meta_output_dir, **meta_kwargs)
        self.cits_validator = Validator(self.cits_csv_doc, self.cits_output_dir, **cits_kwargs)

        self.helper = Helper()

        # Check if each of the two Validator instances is passed the expected table type
        if self.meta_validator.table_to_process != 'meta_csv':
            raise TableNotMatchingInstance(self.meta_csv_doc, self.meta_validator.table_to_process, 'meta_csv')
        if self.cits_validator.table_to_process != 'cits_csv':
            raise TableNotMatchingInstance(self.cits_csv_doc, self.cits_validator.table_to_process, 'cits_csv')


    def check_closure(self):

        ids_positions_meta = dict()
        ids_positions_cits = dict()
        meta_br_ids_groups = []
        cits_br_ids_groups = []
        
        meta_json_report = []
        cits_json_report = []

        # Collect entities in META
        for row_idx, row in enumerate(self.meta_validator.data):
            if row.get('id'):
                ids:list = [i.strip() for i in row['id'].split()]
                meta_br_ids_groups.append(set(ids))
                for item in set(ids):
                    if not ids_positions_meta.get(item):
                        ids_positions_meta[item] = [{row_idx: {'id': list(range(len(ids)))}}]
                    else:
                        ids_positions_meta[item].append({row_idx: {'id': list(range(len(ids)))}})

        # Collect entities in CITS-CSV
        for row_idx, row in enumerate(self.cits_validator.data):
            if row.get('citing_id'):
                ids:list = [i.strip() for i in row['citing_id'].split()]
                cits_br_ids_groups.append(set(ids))
                for item in set(ids):
                    if not ids_positions_cits.get(item):
                        ids_positions_cits[item] = [{row_idx: {'citing_id': list(range(len(ids)))}}]
                    else:
                        ids_positions_cits[item].append({row_idx: {'citing_id': list(range(len(ids)))}})
            if row.get('cited_id'):
                ids:list = [i.strip() for i in row['cited_id'].split()]
                cits_br_ids_groups.append(set(ids))
                for item in set(ids):
                    if not ids_positions_cits.get(item):
                        ids_positions_cits[item] = [{row_idx: {'cited_id': list(range(len(ids)))}}]
                    else:
                        ids_positions_cits[item].append({row_idx: {'cited_id': list(range(len(ids)))}})

        ids_with_metadata = set(ids_positions_meta.keys())
        ids_in_citations = set(ids_positions_cits.keys())
        meta_ids_missing_citations = ids_with_metadata.difference(ids_in_citations) # entities that have metadata but are not involved in any citation
        cits_ids_missing_metadata = ids_in_citations.difference(ids_with_metadata) # entities that are represented in citations but have no metadata

        meta_entities = self.helper.group_ids(meta_br_ids_groups) # list of sets where each set uniquely contains the ids of a single BR as it is represented in META-CSV
        cits_entities = self.helper.group_ids(cits_br_ids_groups) # list of sets where each set uniquely contains the ids of a single BR as it is represented in CITS-CSV

        if meta_ids_missing_citations:
            for br_ids_set in meta_entities: # Write an error instance FOR EACH BR, not for each ID
                table = dict()
                # Check if all of the IDs associated with the current BR are in meta_ids_missing_citations (using .issubset), 
                # i.e., if none of the IDs for this BR is involved in a citation. If you want to write an error even when just one
                # of the IDs is not involved in a citation, chech if br_ids_set.intersection(meta_ids_missing_citations) instead.
                if br_ids_set.issubset(meta_ids_missing_citations):
                    # for i in br_ids_set.intersection(meta_ids_missing_citations):
                    for i in br_ids_set:
                        for d in ids_positions_meta[i]:
                            table.update(d)
                    meta_json_report.append(
                        self.helper.create_error_dict(
                            validation_level='csv_wellformedness',
                            error_type='error',
                            message=self.messages['m24'], 
                            error_label='missing_citations',
                            located_in='row',
                            table=table
                        )
                    )

        if cits_ids_missing_metadata:
            for br_ids_set in cits_entities: # Write an error instance FOR EACH BR, not for each ID
                table = dict()
                # Check if all of the IDs associated with the current BR are in cits_ids_missing_metadata (using .issubset), 
                # i.e., if none of the IDs for this BR has available metadata. If you want to write an error even when just one
                # of the IDs has no metadata, chech if br_ids_set.intersection(cits_ids_missing_metadata) instead.
                if br_ids_set.issubset(cits_ids_missing_metadata):
                    # for i in br_ids_set.intersection(cits_ids_missing_metadata):
                    for i in br_ids_set:
                        for d in ids_positions_cits[i]:
                            table.update(d)
                    cits_json_report.append(
                        self.helper.create_error_dict(
                            validation_level='csv_wellformedness',
                            error_type='error',
                            message=self.messages['m25'],
                            error_label='missing_metadata',
                            located_in='row',
                            table=table
                        )
                    )
        
        meta_txt_report = self.helper.create_validation_summary(meta_json_report)
        cits_txt_report = self.helper.create_validation_summary(cits_json_report)

        return (meta_json_report, meta_txt_report, cits_json_report, cits_txt_report)
        

    def validate(self):

        # TODO: add informative print messages to say which process is running and when it terminates
        
        # Run single validation for META-CSV and CITS-CSV
        meta_out = self.meta_validator.validate()
        cits_out = self.cits_validator.validate()

        # in case some errors have already been found and strict_sequentiality is True, don't run the check on closure
        if self.strict_sequentiality and (meta_out or cits_out):
            print('The separate validation of the metadata (META-CSV) and citations (CITS-CSV) tables already detected some error (in one or both documents).',
                  'Skipping the check of transitive closure as strict_sequentiality==True.')
            return (meta_out, cits_out) 
        
        # Run validation for transitive closure
        closure_check_out = self.check_closure()
        meta_closure_json = closure_check_out[0]
        meta_closure_txt = closure_check_out[1]
        cits_closure_json = closure_check_out[2]
        cits_closure_txt = closure_check_out[3]

        # META-CSV
        # append result of check_closure to the existing JSON validation report
        with open(self.meta_validator.output_fp_json, 'r', encoding='utf-8') as f:
            existing_meta_json:list = load(f)
            final_meta_json = existing_meta_json + meta_closure_json
        with open(self.meta_validator.output_fp_json, 'w', encoding='utf-8') as f:
            dump(final_meta_json, f, indent=4)

        # append result of check_closure to the existing TXT validation report
        with open(self.meta_validator.output_fp_txt, "a", encoding='utf-8') as f:
            f.write(meta_closure_txt)

        # CITS-CSV
        # append to JSON (CITS-CSV)
        with open(self.cits_validator.output_fp_json, 'r', encoding='utf-8') as f:
            existing_cits_json:list = load(f)
            final_cits_json = existing_cits_json + cits_closure_json
        with open(self.cits_validator.output_fp_json, 'w', encoding='utf-8') as f:
            dump(final_cits_json, f, indent=4)
        # append to TXT (CITS-CSV)
        with open(self.cits_validator.output_fp_txt, "a", encoding='utf-8') as f:
            f.write(cits_closure_txt)

        return (final_meta_json, final_cits_json)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', dest='input_csv', required=True,
                        help='The path to the CSV document to validate.', type=str)
    parser.add_argument('-o', '--output', dest='output_dir', required=True,
                        help='The path to the directory where to store the output JSON file.', type=str)
    parser.add_argument('-m', '--use-meta', dest='use_meta_endpoint', action='store_true',
                        help='Use the OC Meta endpoint to check if an ID exists.', required=False)
    parser.add_argument('-s', '--no-id-existence', dest='verify_id_existence', action='store_false',
                        help='Skip checking if IDs are registered somewhere, i.e. do not use Meta endpoint nor external APIs.',
                        required=False)
    args = parser.parse_args()
    v = Validator(args.input_csv, args.output_dir, args.use_meta_endpoint)
    v.validate()

# to instantiate the class, write:
# v = Validator('path/to/csv/file', 'output/dir/path') # optionally set use_meta_endpoint to True and/or verify_id_existence to False
# v.validate() --> validates, returns the output, and saves files


# FROM THE COMMAND LINE:
# python -m oc_validator.main -i <input csv file path> -o <output dir path> [-m] [-s]
