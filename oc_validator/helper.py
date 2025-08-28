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

from collections import defaultdict


class UnionFind:
    def __init__(self):
        self.parent = dict()

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, x, y):
        self.parent[self.find(x)] = self.find(y)

class Helper:
    def __init__(self):  # todo: è necessario mettere init?
        self.descr = 'contains helper functions'

    # # THIS IS THE OLD FUNCTION TO GROUP IDS, KEPT HERE FOR REFERENCE
    # def group_ids(self, id_groups: list):
    #     """
    #     Divides identifiers in a list of sets, where each set corresponds to a bibliographic entity.
    #     Takes in input a list of sets where each set represent the field 'citing_id', 'cited_id' or 'id' of a single row.
    #     Two IDs are considered to be associated to the same bibliographic entity if they occur together in a set at
    #     least once.
    #     :param id_groups: list containing sets of formally valid IDs
    #     :return: list of sets grouping the IDs associated to the same bibliographic entity
    #     """
    #     old_len = len(id_groups) + 1
    #     while len(id_groups) < old_len:
    #         old_len = len(id_groups)
    #         for i in range(len(id_groups)):
    #             for j in range(i + 1, len(id_groups)):
    #                 if len(id_groups[i] & id_groups[j]):
    #                     id_groups[i] = id_groups[i] | id_groups[j]
    #                     id_groups[j] = set()
    #         id_groups = [id_groups[i] for i in range(len(id_groups)) if id_groups[i] != set()]

    #     return id_groups

    def group_ids(self, id_groups: list[set]) -> list[set]:

        uf = UnionFind()

        # Union all IDs that appear together in a group
        for group in id_groups:
            ids = list(group)
            for i in range(1, len(ids)):
                uf.union(ids[0], ids[i])

        # Gather groups
        components = defaultdict(set)
        for group in id_groups:
            for id_ in group:
                root = uf.find(id_)
                components[root].add(id_)

        return list(components.values())

    def create_error_dict(self, validation_level: str, error_type: str, message: str, error_label: str, located_in: str,
                          table: dict, valid=False):
        """
        Creates a dictionary representing the error, i.e. the negative output of a validation function.
        :param validation_level: one of the following values: "csv_wellformedness", "external_syntax", "semantic".
        :param error_type: one of the following values: "error", "warning".
        :param error_label: a machine-readable label, connected to one and only one validating function.
        :param message: the message for the user.
        :param located_in: the type of the table's area where the error is located; one of the following values: "row, "field", "item".
        :param table: the tree representing the exact location of all the elements that make the error.
        :param valid = flag for specifying whether the data raising the error is still valid or not. Defaults to False, meaning that the error makes the whole document invalid.
        :return: the details of a specific error, as it is detected by executing a validation function.
        """

        position = {
            'located_in': located_in,
            'table': table
        }

        result = {
            'validation_level': validation_level,
            'error_type': error_type,
            'error_label': error_label,
            'valid': valid,
            # todo: consider removing 'valid' if for all warnings 'valid'=True and for all errors 'valid'=False
            'message': message,
            'position': position
        }

        return result

    def create_validation_summary(self, error_report):
        """
        Creates a natural language summary of the validation error report.
        :param error_report:
        :return:
        """

        # Count the number of instances of each error label
        error_counts = {}
        for error in error_report:
            label = error['error_label']
            error_counts[label] = error_counts.get(label, 0) + 1

        label_report = []
        for label, count in error_counts.items():
            errors_with_label = [e for e in error_report if e['error_label'] == label]
            explanation = errors_with_label[0]['message']  # all errors w/ a given label have the same message
            instance_details = []
            count_summary = f"There are {count} {label} issues in the document." if count > 1 else f"There is {count} {label} issue in the document. "
            for err_idx, error in enumerate(errors_with_label):
                tree = error['position']['table']
                all_locs = []
                for row_node_pos, row_node_value in tree.items():
                    involved_row = row_node_pos
                    for field_node_name, field_node_value in row_node_value.items():
                        involved_field = field_node_name
                        involved_items = field_node_value
                        single_node_pos = f"row {involved_row}, field {involved_field}, and items in position {involved_items}"
                        all_locs.append(single_node_pos)

                if len(all_locs) > 1:
                    location = f""
                    pointer = 0
                    while pointer < len(all_locs):
                        location = location + all_locs[pointer] + "; "
                        pointer += 1
                    else:
                        location = location[:-2]
                else:
                    location = f"{all_locs[0]}"

                # Construct a detailed message for each error
                if len(errors_with_label) > 1:
                    detail = f"- {error['error_type']} {err_idx + 1} involves: {location}."
                else:
                    detail = f"- The {error['error_type']} involves: {location}."
                instance_details.append(detail)

            # Combine the summary and detailed messages for the current error label
            error_label_summary = count_summary + "\n" + explanation + "\n".join(instance_details)
            label_report.append(error_label_summary)

        # Combine all the error messages into a single string
        report = "\n\n".join(label_report)
        return report
