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
from os.path import exists, join, dirname
from os import makedirs, getcwd
from re import finditer
from oc_validator.helper import Helper
from oc_validator.csv_wellformedness import Wellformedness
from oc_validator.id_syntax import IdSyntax
from oc_validator.id_existence import IdExistence
from oc_validator.semantics import Semantics
from argparse import ArgumentParser


class Validator:
    def __init__(self, csv_doc: str, output_dir: str):
        self.data = self.read_csv(csv_doc)
        self.table_to_process = self.process_selector(self.data)
        self.helper = Helper()
        self.wellformed = Wellformedness()
        self.syntax = IdSyntax()
        self.existence = IdExistence()
        self.semantics = Semantics()
        self.messages = full_load(open('oc_validator/messages.yaml', 'r', encoding='utf-8'))
        # self.messages = full_load(open(join(dirname(__file__), 'messages.yaml'), 'r', encoding='utf-8'))
        self.id_type_dict = load(
            open('oc_validator/id_type_alignment.json', 'r', encoding='utf-8'))  # for ID-type alignment (semantics)
        self.output_dir = output_dir
        if not exists(self.output_dir):
            makedirs(self.output_dir)

    def read_csv(self, csv_doc):
        with open(csv_doc, 'r', encoding='utf-8') as f:
            data_dict = list(DictReader(f))
            return data_dict

    def process_selector(self, data: list):
        process_type = None
        try:
            if all(set(row.keys()) == {"id", "title", "author", "pub_date", "venue", "volume", "issue", "page", "type",
                                        "publisher", "editor"} for row in data):
                process_type = 'meta_csv'
                return process_type
            elif all(set(row.keys()) == {'citing_id', 'citing_publication_date', 'cited_id', 'cited_publication_date'}
                     for row in
                     data):
                process_type = 'cits_csv'
                return process_type
            else:
                return process_type
        except KeyError:
            print('The submitted table cannot be read as neither META-CSV nor CITS-CSV')
            return process_type

    def validate(self):
        if self.table_to_process == 'meta_csv':
            return self.validate_meta()
        elif self.table_to_process == 'cits_csv':
            return self.validate_cits()
        else:
            return "The input table is not processable, since it does not comply with neither META-CSV nor CITS-CSV basic structure"

    def validate_meta(self) -> list:
        """
        Validate an instance of META-CSV
        :return: the list of errors, i.e. the report of the validation process
        """
        error_final_report = []

        messages = self.messages
        id_type_dict = self.id_type_dict

        br_id_groups = []

        for row_idx, row in enumerate(self.data):
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
                                elif not self.existence.check_id_existence(item):
                                    message = messages['m20']
                                    table = {row_idx: {field: [item_idx]}}
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
                                    elif not self.existence.check_id_existence(id):
                                        message = messages['m22']
                                        table = {row_idx: {field: [item_idx]}}
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
                                   finditer(r'((?:doi|issn|isbn|url|wikidata|wikipedia|openalex):\S+)(?=\s|\])', value)]

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
                                elif not self.existence.check_id_existence(id):
                                    message = messages['m20']
                                    table = {row_idx: {field: [0]}}
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
                        if self.wellformed.orphan_ra_id(value):
                            message = messages['m10']
                            table = {row_idx: {field: [0]}}
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
                            table = {row_idx: {field: [0]}}
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
                                    table = {row_idx: {field: [0]}}
                                    error_final_report.append(
                                        self.helper.create_error_dict(validation_level='external_syntax',
                                                                      error_type='error',
                                                                      message=message,
                                                                      error_label='ra_id_syntax',
                                                                      located_in='item',
                                                                      table=table))
                                #  3rd validation level: EXISTENCE OF ID (RESPONSIBLE AGENT)
                                elif not self.existence.check_id_existence(id):
                                    message = messages['m22']
                                    table = {row_idx: {field: [0]}}
                                    error_final_report.append(
                                        self.helper.create_error_dict(validation_level='existence',
                                                                      error_type='warning',
                                                                      message=message,
                                                                      error_label='ra_id_existence',
                                                                      located_in='item',
                                                                      table=table, valid=True))

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
        with open(join(self.output_dir, 'out_validate_meta.json'), 'w', encoding='utf-8') as f:
            dump(error_final_report, f)

        # write human-readable validation summary to txt file
        textual_report = self.helper.create_validation_summary(error_final_report)
        with open(join(self.output_dir, "meta_validation_summary.txt"), "w", encoding='utf-8') as f:
            f.write(textual_report)

        return error_final_report

    def validate_cits(self) -> list:
        """
        Validates an instance of CITS-CSV.
        :return: the list of errors, i.e. the report of the validation process
        """

        error_final_report = []

        messages = full_load(open('oc_validator/messages.yaml', 'r', encoding='utf-8'))

        id_fields_instances = []

        for row_idx, row in enumerate(self.data):
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
                                elif not self.existence.check_id_existence(item):
                                    message = messages['m20']
                                    table = {row_idx: {field: [item_idx]}}
                                    error_final_report.append(
                                        self.helper.create_error_dict(validation_level='existence',
                                                                      error_type='warning',
                                                                      message=message,
                                                                      error_label='br_id_existence',
                                                                      located_in='item',
                                                                      table=table,
                                                                      valid=True))

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
        with open(join(self.output_dir, 'out_validate_cits.json'), 'w', encoding='utf-8') as f:
            dump(error_final_report, f)

        # write human-readable validation summary to txt file
        textual_report = self.helper.create_validation_summary(error_final_report)
        with open(join(self.output_dir, "cits_validation_summary.txt"), "w", encoding='utf-8') as f:
            f.write(textual_report)

        return error_final_report


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', dest='input_csv', required=True,
                        help='The path to the CSV document to validate.', type=str)
    parser.add_argument('-o', '--output', dest='output_dir', required=True,
                        help='The path to the directory where to store the output JSON file.', type=str)
    args = parser.parse_args()
    v = Validator(args.input_csv, args.output_dir)
    v.validate()

# to instantiate the class, write:
# v = Validator('path/to/csv/file', 'output/dir/path')
# v.validate() --> validates, returns the output, and saves files


# FROM THE COMMAND LINE:
# python -m oc_validator.main -i <input csv file path> -o <output dir path>
