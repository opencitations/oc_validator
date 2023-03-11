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

from oc_idmanager import doi, isbn, issn, orcid, pmcid, pmid, ror, url, viaf, wikidata, wikipedia

class IdSyntax:

    def __init__(self):
        pass

    def check_id_syntax(self, id: str):
        """
        Checks the specific external syntax of each identifier schema, calling the syntax_ok() method from every
        IdManager class.
        :param id: the identifier (with its prefix)
        :return: bool
        """
        oc_prefix = id[:(id.index(':') + 1)]

        if oc_prefix == 'doi:':
            vldt = doi.DOIManager()
            return vldt.syntax_ok(id)
        if oc_prefix == 'isbn:':
            vldt = isbn.ISBNManager()
            return vldt.syntax_ok(id)
        if oc_prefix == 'issn:':
            vldt = issn.ISSNManager()
            return vldt.syntax_ok(id)
        if oc_prefix == 'orcid:':
            vldt = orcid.ORCIDManager()
            return vldt.syntax_ok(id)
        if oc_prefix == 'pmcid:':
            vldt = pmcid.PMCIDManager()
            return vldt.syntax_ok(id)
        if oc_prefix == 'pmid:':
            vldt = pmid.PMIDManager()
            return vldt.syntax_ok(id)
        if oc_prefix == 'ror:':
            vldt = ror.RORManager()
            return vldt.syntax_ok(id)
        if oc_prefix == 'url:':
            vldt = url.URLManager()
            return vldt.syntax_ok(id)
        if oc_prefix == 'viaf:':
            vldt = viaf.ViafManager()
            return vldt.syntax_ok(id)
        if oc_prefix == 'wikidata:':
            vldt = wikidata.WikidataManager()
            return vldt.syntax_ok(id)
        if oc_prefix == 'wikipedia:':
            vldt = wikipedia.WikipediaManager()
            return vldt.syntax_ok(id)