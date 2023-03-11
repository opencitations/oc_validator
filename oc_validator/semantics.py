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

class Semantics:
    def __init__(self):
        pass

    def check_semantics(self, row: dict, alignment: dict) -> dict:
        """
        Checks if all the IDs specified in 'id' are compatible with the value of 'type'.
        Return a dictionary with the fields and items involved in the error, or an empty
        dictionary if no error was found.
        :param row: (dict) the row in the table
        :param alignment: (dict) the possible associations between a type and a set of IDs
        :return: (dict)
        """
        invalid_row = {}
        row_type = row['type']
        row_ids = row['id'].split(' ')  # list
        invalid_ids_idxs = []

        if row['type'] and row['id']: # apply semantic checks only if both 'id' and 'type' are not empty
            for id_idx, id in enumerate(row_ids):
                if id[:id.index(':')] not in alignment[row_type]:
                    invalid_ids_idxs.append(id_idx)

        if invalid_ids_idxs:
            invalid_row['id'] = invalid_ids_idxs
            invalid_row['type'] = [0]
        return invalid_row
