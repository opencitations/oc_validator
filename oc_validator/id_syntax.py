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

from oc_ds_converter.oc_idmanager import doi, isbn, issn, orcid, pmcid, pmid, ror, url, viaf, wikidata, wikipedia, openalex, crossref

class IdSyntax:

    def __init__(self):
        self.doi_mngr = doi.DOIManager()
        self.isbn_mngr = isbn.ISBNManager()
        self.issn_mngr = issn.ISSNManager()
        self.orcid_mngr = orcid.ORCIDManager()
        self.pmcid_mngr = pmcid.PMCIDManager()
        self.pmid_mngr = pmid.PMIDManager()
        self.ror_mngr = ror.RORManager()
        self.url_mngr = url.URLManager()
        self.viaf_mngr = viaf.ViafManager()
        self.wikidata_mngr = wikidata.WikidataManager()
        self.wikipedia_mngr = wikipedia.WikipediaManager()
        self.openalex_mngr = openalex.OpenAlexManager()
        self.crossref_mngr = crossref.CrossrefManager()

    def check_id_syntax(self, id: str):
        """
        Checks the specific external syntax of each identifier schema, calling the syntax_ok() method from every
        IdManager class.
        :param id: the identifier (with its prefix)
        :return: bool
        """
        oc_prefix = id[:(id.index(':') + 1)]

        if oc_prefix == 'doi:':
            vldt = self.doi_mngr
        elif oc_prefix == 'isbn:':
            vldt = self.isbn_mngr
        elif oc_prefix == 'issn:':
            vldt = self.issn_mngr
        elif oc_prefix == 'orcid:':
            vldt = self.orcid_mngr
        elif oc_prefix == 'pmcid:':
            vldt = self.pmcid_mngr
        elif oc_prefix == 'pmid:':
            vldt = self.pmid_mngr
        elif oc_prefix == 'ror:':
            vldt = self.ror_mngr
        elif oc_prefix == 'url:':
            vldt = self.url_mngr
        elif oc_prefix == 'viaf:':
            vldt = self.viaf_mngr
        elif oc_prefix == 'wikidata:':
            vldt = self.wikidata_mngr
        elif oc_prefix == 'wikipedia:':
            vldt = self.wikipedia_mngr
        elif oc_prefix == 'openalex:':
            vldt = self.openalex_mngr
        elif oc_prefix == 'crossref:':
            vldt = self.crossref_mngr
        else:
            return False
        return vldt.syntax_ok(id)
