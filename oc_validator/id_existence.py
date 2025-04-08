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

from oc_ds_converter.oc_idmanager import doi, isbn, issn, orcid, pmcid, pmid, ror, url, viaf, wikidata, wikipedia, \
    openalex, crossref, jid, arxiv
from SPARQLWrapper import SPARQLWrapper, JSON
import time


class IdExistence:

    def __init__(self, use_meta_endpoint=True):
        """
        Checks whether an external ID exists or not, by verifying it is registered as such in the appropriate service.
        :param use_meta_endpoint: indicates whether or not to look for an ID in OC Meta triplestore via SPARQL
        endpoint.
        """
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
        self.jid_mngr = jid.JIDManager()
        self.arxiv_mngr = arxiv.ArXivManager()
        self.use_meta_endpoint = use_meta_endpoint
        self.sparql = SPARQLWrapper("https://opencitations.net/meta/sparql")
        self.sparql.addCustomHttpHeader('Authorization', '4c793897-7787-43ff-b7fa-00aaf7ddf7ed')

    def check_id_existence(self, id:str):
        """
        Queries a database to look for the ID passed as argument (with its prefix included). If
        IdExistence.use_meta_endpoint is set to False, it queries only external services and directly returns
        the output of ID.Existence.query_external_service(). If IdExistence.use_meta_endpoint is set to True, it first
        queries OC Meta's SPARQL endpoint (calling IdExistence.query_meta_triplestore()): if the ID is already
        present in Meta, return True; else, queries external service and return the result of this last query.
        :param id: the string of the ID (prefix included)
        :return: bool
        """
        if id.startswith('temp:') or id.startswith('local:'): # temp: and local: internal IDs are always considered as exisiting
            return True
        if id.startswith('omid:'):  # OMID needs to be checked with a specific query on the triplestore
            return self.query_omid_in_meta(id)
        if self.use_meta_endpoint:
            meta_response = self.query_meta_triplestore(id)
            return meta_response if meta_response is True else self.query_external_service(id)
        return self.query_external_service(id)

    def query_external_service(self, id: str):
        """
        Checks if a specific identifier is registered in the service it is provided by, by a request to the relative API,
        calling the .exists() method from every IdManager module.
        :param id: the string of the ID (prefix included)
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
        elif oc_prefix == 'jid:':
            vldt = self.jid_mngr
        elif oc_prefix == 'arxiv:':
            vldt = self.arxiv_mngr
        else:
            return False
        return vldt.exists(id.replace(oc_prefix, '', 1))

    def query_meta_triplestore(self, id:str, retries: int = 3, delay: float = 2.0):
        """
        Checks if an ID exists by looking it up in the OpenCitations Meta triplestore via a SPARQL query to Meta's endpoint.
        :param id: the string of the ID (prefix included)
        :return: bool
        """
        oc_prefix = id[:(id.index(':') + 1)]
        lookup_id = id.replace(oc_prefix, '', 1)
        datacite_id_scheme = oc_prefix[:-1]  # same as OC prefix but without the ":"

        sparql = self.sparql
        q = '''
        PREFIX datacite: <http://purl.org/spar/datacite/>
        PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
        ASK {
            ?identifier literal:hasLiteralValue "%s".
            ?res datacite:hasIdentifier ?identifier.
            ?identifier datacite:usesIdentifierScheme datacite:%s.
        }
        ''' % (lookup_id, datacite_id_scheme)

        for attempt in range(retries):
            try:
                sparql.setQuery(q)
                sparql.setReturnFormat(JSON)
                result: dict = sparql.query().convert()
                return result.get('boolean')
            
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)  # wait before retrying
                else:
                    print("Max retries reached. Query failed.")
                    return False
    
    def query_omid_in_meta(self, id:str, retries:int=3, delay:float=2.0):
        """
        Queries exclusively OMIDs in OC Meta, checking if they are registered in the live triplestore.
        :param id: the string of the ID (prefix included)
        :return: bool
        """
        lookup_id = id.replace('omid:', '', 1)

        sparql = self.sparql

        q = '''
        ASK WHERE {
            { <https://w3id.org/oc/meta/%s> ?p ?o } 
        UNION 
            { ?s ?p <https://w3id.org/oc/meta/%s> }
        }
        ''' % (lookup_id, lookup_id)

        for attempt in range(retries):
            try:
                sparql.setQuery(q)
                sparql.setReturnFormat(JSON)
                result: dict = sparql.query().convert()
                return result.get('boolean', False)
            
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)  # wait before retrying
                else:
                    print("Max retries reached. Query failed.")
                    return False