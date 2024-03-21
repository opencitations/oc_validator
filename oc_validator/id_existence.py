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

from oc_ds_converter.oc_idmanager import doi, isbn, issn, orcid, pmcid, pmid, ror, url, viaf, wikidata, wikipedia, openalex

class IdExistence:

    def __init__(self):
        self.doim= doi.DOIManager()
        self.isbnm= isbn.ISBNManager()
        self.issnm= issn.ISSNManager()
        self.orcidm= orcid.ORCIDManager()
        self.pmcidm= pmcid.PMCIDManager()
        self.pmidm= pmid.PMIDManager()
        self.rorm= ror.RORManager()
        self.urlm= url.URLManager()
        self.viafm= viaf.ViafManager()
        self.wikidatam= wikidata.WikidataManager()
        self.wikipediam= wikipedia.WikipediaManager()
        self.openalexm= openalex.OpenAlexManager()

    def check_id_existence(self, id:str):
        """
        Checks if a specific identifier is registered in the service it is provided by, by a request to the relative API,
        calling the .exists() method from every IdManager module.
        :param id: the string of the ID without the prefix
        :return: bool
        """

        oc_prefix = id[:(id.index(':')+1)]

        if oc_prefix == 'doi:':
            vldt = self.doim  # you can use removeprefix(oc_prefix) from Python 3.9+
        elif oc_prefix == 'isbn:':
            vldt = self.isbnm
        elif oc_prefix == 'issn:':
            vldt = self.issnm
        elif oc_prefix == 'orcid:':
            vldt = self.orcidm
        elif oc_prefix == 'pmcid:':
            vldt = self.pmcidm
        elif oc_prefix == 'pmid:':
            vldt = self.pmidm
        elif oc_prefix == 'ror:':
            vldt = self.rorm
        elif oc_prefix == 'url:':
            vldt = self.urlm
        elif oc_prefix == 'viaf:':
            vldt = self.viafm
        elif oc_prefix == 'wikidata:':
            vldt = self.wikidatam
        elif oc_prefix == 'wikipedia:':
            vldt = self.wikipediam
        elif oc_prefix == 'openalex:':
            vldt = self.openalexm
        # todo: add Crossref ID for publishers (currently not in id_manager)
        else:
            return False
        return vldt.exists(id.replace(oc_prefix, '', 1))
