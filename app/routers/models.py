"""Model API router."""

import logging
from pprint import pprint
from typing import List

import requests
from fastapi import APIRouter, Path, Query
from gocam.translation.minerva_wrapper import MinervaWrapper
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.resource import OntologyResource

from app.exceptions.global_exceptions import DataNotFoundException, InvalidIdentifier
from app.utils import ontology_utils
from app.utils.settings import get_sparql_endpoint, get_user_agent
from app.utils.sparql_utils import transform_array

USER_AGENT = get_user_agent()
SPARQL_ENDPOINT = get_sparql_endpoint()
router = APIRouter()

logger = logging.getLogger()


@router.get(
    "/api/gocam-model/{id}",
    tags=["models"],
    description="Returns model details in gocam-py format based on a GO-CAM model ID.",
)
async def get_gocam_model_by_id_in_gocam_py_format(
    id: str = Path(
        ...,
        description="A GO-CAM identifier (e.g. 581e072c00000820, 581e072c00000295, 5900dc7400000968)",
        examples=["581e072c00000295"],
    )
) -> dict:
    """
    Returns model details in gocam-py format based on a GO-CAM model ID.

    :param id: A GO-CAM identifier (e.g. 581e072c00000820, 581e072c00000295, 5900dc7400000968)
    :return: model details in gocam-py format based on a GO-CAM model ID.
    """
    mw = MinervaWrapper()
    stripped_ids = []
    if id.startswith("gomodel:"):
        model_id = id.replace("gomodel:", "")
        stripped_ids.append(model_id)
    else:
        stripped_ids.append(id)
    for stripped_id in stripped_ids:
        path_to_s3 = "https://go-public.s3.amazonaws.com/files/go-cam/%s.json" % stripped_id
        print(path_to_s3)
        try:
            response = requests.get(path_to_s3, timeout=30, headers={"User-Agent": USER_AGENT})
            # Check for 403/404 first before trying to parse JSON or raise_for_status
            if response.status_code == 403 or response.status_code == 404:
                raise DataNotFoundException("GO-CAM model not found.")

            # Now try to raise_for_status for other error codes
            response.raise_for_status()

            # If we get here, we have a valid response
            data = response.json()
            gocam_reposnse = mw.minerva_object_to_model(data)  # convert minerva object to gocam model
            pprint(gocam_reposnse)
            return gocam_reposnse.model_dump()
        except DataNotFoundException:
            # Re-raise without modification to keep the 404 status
            raise
        except requests.exceptions.JSONDecodeError as json_err:
            # Invalid JSON response
            raise DataNotFoundException("GO-CAM model response was invalid") from json_err
        except Exception as e:
            # Log the error for debugging but return a 404 for not found models
            logger.error(f"Error retrieving model {stripped_id}: {str(e)}")
            raise DataNotFoundException("GO-CAM model not found") from e


@router.get("/api/models/go", tags=["models"], description="Returns go term details based on a GO-CAM model ID.")
async def get_goterms_by_model_id(
    gocams: List[str] = Query(
        None,
        description="A list of GO-CAM IDs separated by a comma, e.g. 59a6110e00000067,SYNGO_369",
        examples=["581e072c00000295", "SYNGO_369"],
    )
):
    """Returns go term details based on a GO-CAM model ID."""
    stripped_ids = []
    for model_id in gocams:
        if model_id.startswith("gomodel:"):
            model_id = id.replace("gomodel:", "")
            stripped_ids.append(model_id)
        else:
            stripped_ids.append(model_id)
    for stripped_id in stripped_ids:
        path_to_s3 = "https://go-public.s3.amazonaws.com/files/go-cam/%s.json" % stripped_id
        response = requests.get(path_to_s3, timeout=30, headers={"User-Agent": USER_AGENT})
        if response.status_code == 403 or response.status_code == 404:
            raise DataNotFoundException("GO-CAM model not found.")

    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    gocam = ""
    if stripped_ids:
        for model in stripped_ids:
            if gocam == "":
                gocam = "<http://model.geneontology.org/" + model + "> "
            else:
                gocam = gocam + "<http://model.geneontology.org/" + model + "> "
        query = (
            """
            PREFIX metago: <http://model.geneontology.org/>
            PREFIX definition: <http://purl.obolibrary.org/obo/IAO_0000115>
            PREFIX BP: <http://purl.obolibrary.org/obo/GO_0008150>
            PREFIX MF: <http://purl.obolibrary.org/obo/GO_0003674>
            PREFIX CC: <http://purl.obolibrary.org/obo/GO_0005575>
            SELECT distinct ?gocam ?goclasses ?goids ?gonames ?definitions
            WHERE
            {
                VALUES ?gocam { %s }
                GRAPH ?gocam {
                    ?entity rdf:type owl:NamedIndividual .
                    ?entity rdf:type ?goids
                }

                VALUES ?goclasses { BP: MF: CC:  } .
                ?goids rdfs:subClassOf+ ?goclasses .
                ?goids rdfs:label ?gonames .
                ?goids definition: ?definitions .
            }
            ORDER BY DESC(?gocam)
        """
            % gocam
        )
    else:
        query = """

        PREFIX metago: <http://model.geneontology.org/>
        PREFIX definition: <http://purl.obolibrary.org/obo/IAO_0000115>
        PREFIX BP: <http://purl.obolibrary.org/obo/GO_0008150>
        PREFIX MF: <http://purl.obolibrary.org/obo/GO_0003674>
        PREFIX CC: <http://purl.obolibrary.org/obo/GO_0005575>

		SELECT distinct ?gocam ?goclasses ?goids ?gonames ?definitions
        WHERE
        {

  		    GRAPH ?gocam {
    			?gocam metago:graphType metago:noctuaCam  .
                ?entity rdf:type owl:NamedIndividual .
    			?entity rdf:type ?goids
            }

            VALUES ?goclasses { BP: MF: CC:  } .
            # rdf:type faster then subClassOf+ but require filter
            # ?goids rdfs:subClassOf+ ?goclasses .
    		?entity rdf:type ?goclasses .

  			# Filtering out the root BP, MF & CC terms
			filter(?goids != MF: )
  			filter(?goids != BP: )
		  	filter(?goids != CC: )

  			# then getting their definitions
    		?goids rdfs:label ?gonames .
  		    ?goids definition: ?definitions .
        }
		ORDER BY DESC(?gocam)
        """

    results = si._sparql_query(query)
    summary_gocam = ""
    collated = {}
    collated_results = []
    for result in results:
        if summary_gocam == "":
            collated["goclasses"] = [result["goclasses"].get("value")]
            collated["goids"] = [result["goids"].get("value")]
            collated["gonames"] = [result["gonames"].get("value")]
            collated["definitions"] = [result["definitions"].get("value")]
            collated["gocam"] = result["gocam"].get("value")
            summary_gocam = result["gocam"].get("value")
        elif summary_gocam == result["gocam"].get("value"):
            collated["goclasses"].append(result["goclasses"].get("value"))
            collated["goids"].append(result["goids"].get("value"))
            collated["gonames"].append(result["gonames"].get("value"))
            collated["definitions"].append(result["definitions"].get("value"))
        else:
            collated_results.append(collated)
            collated = {}
            summary_gocam = result["gocam"].get("value")
            collated["goclasses"] = [result["goclasses"].get("value")]
            collated["goids"] = [result["goids"].get("value")]
            collated["gonames"] = [result["gonames"].get("value")]
            collated["definitions"] = [result["definitions"].get("value")]
            collated["gocam"] = result["gocam"].get("value")
    collated_results.append(collated)
    return collated_results


@router.get("/api/models/gp", tags=["models"], description="Returns gene product details based on a GO-CAM model ID.")
async def get_geneproducts_by_model_id(
    gocams: List[str] = Query(
        None,
        description="A list of GO-CAM IDs separated by a comma, e.g. 59a6110e00000067,SYNGO_369",
        examples=["581e072c00000295", "SYNGO_369"],
    )
):
    """
    Returns gene product details based on a GO-CAM model ID.

    :param gocams: A list of GO-CAM IDs separated by a comma, e.g. 59a6110e00000067,SYNGO_369
    :return: gene product details based on a GO-CAM model ID.
    """
    stripped_ids = []
    for model_id in gocams:
        if model_id.startswith("gomodel:"):
            model_id = model_id.replace("gomodel:", "")
            stripped_ids.append(model_id)
        else:
            stripped_ids.append(model_id)
    for stripped_id in stripped_ids:
        path_to_s3 = "https://go-public.s3.amazonaws.com/files/go-cam/%s.json" % stripped_id
        response = requests.get(path_to_s3, timeout=30, headers={"User-Agent": USER_AGENT})
        if response.status_code == 403 or response.status_code == 404:
            raise DataNotFoundException("GO-CAM model not found.")

    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    gocam = ""
    if stripped_ids:
        for model in stripped_ids:
            if gocam == "":
                gocam = "<http://model.geneontology.org/" + model + "> "
            else:
                gocam = gocam + "<http://model.geneontology.org/" + model + "> "
        query = (
            """
            PREFIX metago: <http://model.geneontology.org/>
            PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
            PREFIX in_taxon: <http://purl.obolibrary.org/obo/RO_0002162>
            SELECT ?gocam   (GROUP_CONCAT(distinct ?identifier; separator="@|@") as ?gpids)
                            (GROUP_CONCAT(distinct ?name; separator="@|@") as ?gpnames)
            WHERE
            {
                VALUES ?gocam { %s }

                GRAPH ?gocam {
                    ?s enabled_by: ?gpnode .
                    ?gpnode rdf:type ?identifier .
                    FILTER(?identifier != owl:NamedIndividual) .
                }
                optional {
                    GRAPH <http://purl.obolibrary.org/obo/go/extensions/go-graphstore.owl> {
                        ?identifier rdfs:label ?name
                    }
                }
            }
            GROUP BY ?gocam
        """
            % gocam
        )
    else:
        query = """
        PREFIX metago: <http://model.geneontology.org/>

        PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
        PREFIX in_taxon: <http://purl.obolibrary.org/obo/RO_0002162>

        SELECT ?gocam   (GROUP_CONCAT(distinct ?identifier; separator="@|@") as ?gpids)
			        	(GROUP_CONCAT(distinct ?name; separator="@|@") as ?gpnames)

        WHERE
        {
            GRAPH ?gocam {
                ?gocam metago:graphType metago:noctuaCam .
                ?s enabled_by: ?gpnode .
                ?gpnode rdf:type ?identifier .
                FILTER(?identifier != owl:NamedIndividual) .
                FILTER(!contains(str(?gocam), "_inferred"))
            }
            optional {
                ?identifier rdfs:label ?name
            }
            BIND(IF(bound(?name), ?name, ?identifier) as ?name)
        }
        GROUP BY ?gocam
        """
    results = si._sparql_query(query)
    results = transform_array(results, ["gpids", "gpnames"])
    return results


@router.get("/api/models/pmid", tags=["models"], description="Returns PMID details based on a GO CAM ID.")
async def get_pmid_by_model_id(
    gocams: List[str] = Query(
        None,
        description="A list of GO-CAM IDs separated by a comma, e.g. 59a6110e00000067,SYNGO_369",
        examples=["581e072c00000295", "SYNGO_369"],
    )
):
    """Returns pubmed details based on a GO CAM id."""
    stripped_ids = []
    for model_id in gocams:
        if model_id.startswith("gomodel:"):
            model_id = model_id.replace("gomodel:", "")
            stripped_ids.append(model_id)
        else:
            stripped_ids.append(model_id)
    for stripped_id in stripped_ids:
        path_to_s3 = "https://go-public.s3.amazonaws.com/files/go-cam/%s.json" % stripped_id
        response = requests.get(path_to_s3, timeout=30, headers={"User-Agent": USER_AGENT})
        if response.status_code == 403 or response.status_code == 404:
            raise DataNotFoundException("GO-CAM model not found.")

    gocam = ""
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    if stripped_ids:
        for model in stripped_ids:
            if gocam == "":
                gocam = "<http://model.geneontology.org/" + model + "> "
            else:
                gocam = gocam + "<http://model.geneontology.org/" + model + "> "
        query = (
            """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>

        SELECT  distinct ?gocam (GROUP_CONCAT(distinct ?source; separator="@|@") as ?sources)
        WHERE
        {
            values ?gocam { %s }
            GRAPH ?gocam {
                ?s dc:source ?source .
                BIND(REPLACE(?source, " ", "") AS ?source) .
                FILTER((CONTAINS(?source, "PMID")))
            }
        }
        GROUP BY ?gocam

        """
            % gocam
        )
    else:
        query = """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>

        SELECT  distinct ?gocam (GROUP_CONCAT(distinct ?source; separator="` + separator + `") as ?sources)
        WHERE
        {
            GRAPH ?gocam {
                ?gocam metago:graphType metago:noctuaCam .
                ?s dc:source ?source .
                BIND(REPLACE(?source, " ", "") AS ?source) .
                FILTER((CONTAINS(?source, "PMID")))
            }
        }
        GROUP BY ?gocam
        """
    results = si._sparql_query(query)
    collated_results = []
    for result in results:
        collated = {"gocam": result["gocam"].get("value"), "sources": result["sources"].get("value")}
        collated_results.append(collated)
    return collated_results


@router.get(
    "/api/go-cam/{id}", tags=["models"], description="Returns model details based on a GO-CAM model ID in JSON format."
)  # note: this is the endpoint that is currently used by gocam-py to for use in CTX export.
async def get_model_details_by_model_id_json(
    id: str = Path(
        ...,
        description="A GO-CAM identifier (e.g. 581e072c00000820, 581e072c00000295, 5900dc7400000968)",
        examples=["gomodel:66187e4700001573"],
    )
):
    """
    Returns model details based on a GO-CAM model ID in JSON format.

    :param id: A GO-CAM identifier (e.g. 581e072c00000820, 581e072c00000295, 5900dc7400000968)
    :return: model details based on a GO-CAM model ID in JSON format from the S3 bucket.
    """
    stripped_ids = []
    if id.startswith("gomodel:"):
        model_id = id.replace("gomodel:", "")
        stripped_ids.append(model_id)
    else:
        stripped_ids.append(id)
    for stripped_id in stripped_ids:
        path_to_s3 = "https://go-public.s3.amazonaws.com/files/go-cam/%s.json" % stripped_id
        response = requests.get(path_to_s3, timeout=30, headers={"User-Agent": USER_AGENT})
        if response.status_code == 403 or response.status_code == 404:
            raise DataNotFoundException("GO-CAM model not found.")
        else:
            response = requests.get(path_to_s3, timeout=30, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned
            # an unsuccessful status code
            return response.json()


@router.get("/api/models/{id}", tags=["models"], description="Returns model details based on a GO-CAM model ID.")
async def get_term_details_by_model_id(
    id: str = Path(
        ...,
        description="A GO-CAM identifier (e.g. 581e072c00000820, 581e072c00000295, 5900dc7400000968)",
        examples=["581e072c00000295"],
    )
):
    """Returns model details based on a GO-CAM model ID."""
    if id.startswith("gomodel:"):
        replaced_id = id.replace("gomodel:", "")
    else:
        replaced_id = id

    path_to_s3 = "https://go-public.s3.amazonaws.com/files/go-cam/%s.json" % replaced_id
    response = requests.get(path_to_s3, timeout=30, headers={"User-Agent": USER_AGENT})
    if response.status_code == 403 or response.status_code == 404:
        raise DataNotFoundException("GO-CAM model not found.")

    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = (
        """
        PREFIX metago: <http://model.geneontology.org/>

        SELECT ?subject ?predicate ?object
        WHERE
        {
            GRAPH metago:%s {
                ?subject ?predicate ?object
            }
        }
    """
        % id
    )
    results = si._sparql_query(query)
    collated_results = []
    for result in results:
        collated = {
            "subject": result["subject"].get("value"),
            "predicate": result["predicate"].get("value"),
            "object": result["object"].get("value"),
        }
        collated_results.append(collated)
    return collated_results


@router.get("/api/taxon/{taxon}/models", tags=["models"], description="Returns model details based on a NCBI Taxon ID.")
async def get_term_details_by_taxon_id(
    taxon: str = Path(
        ...,
        description="A taxon identifier (e.g. NCBITaxon:9606, NCBITaxon:10090, NCBITaxon:10116)",
        examples=["NCBITaxon:9606"],
    )
):
    """Returns model details based on a NCBI Taxon ID."""
    try:
        ontology_utils.is_golr_recognized_curie(taxon)
    except DataNotFoundException as e:
        raise DataNotFoundException(detail=str(e)) from e
    except ValueError as e:
        raise InvalidIdentifier(detail=str(e)) from e

    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    final_taxon = "http://purl.obolibrary.org/obo/"
    if taxon.startswith("NCBITaxon:"):
        new_taxon = taxon.replace("NCBITaxon:", "NCBITaxon_")
        final_taxon = final_taxon + new_taxon
    query = (
        """
            PREFIX metago: <http://model.geneontology.org/>
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
            PREFIX in_taxon: <http://purl.obolibrary.org/obo/RO_0002162>
            PREFIX pav: <http://purl.org/pav/>
            PREFIX prov: <http://www.w3.org/ns/prov#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX biolink: <https://w3id.org/biolink/vocab/>

            SELECT ?gocam

            WHERE
                {
                    ?gocam rdf:type owl:Ontology ;
                    biolink:in_taxon <%s> ;

                }
    """
        % final_taxon
    )
    results = si._sparql_query(query)
    collated_results = []
    for result in results:
        collated = {"gocam": result["gocam"].get("value")}
        collated_results.append(collated)
    return collated_results


@router.get(
    "/api/pmid/{id}/models",
    tags=["models"],
    description="Returns models for a given publication identifier (PMID).",
)
async def get_model_details_by_pmid(
    id: str = Path(..., description="A publication identifier (PMID)" " (e.g. 15314168 or 26954676)")
):
    """Returns models for a given publication identifier (PMID)."""
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)

    query = (
        """
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        SELECT distinct ?gocam
        WHERE
        {
            GRAPH ?gocam {
                ?gocam metago:graphType metago:noctuaCam .
                ?s dc:source ?source .
                BIND(REPLACE(?source, " ", "") AS ?source) .
                FILTER((CONTAINS(?source, \""""
        + id
        + """\")))
            }
        }
    """
    )
    results = si._sparql_query(query)
    collated_results = []
    collated = {}
    for result in results:
        collated["gocam"] = result["gocam"].get("value")
        collated_results.append(collated)
    if not collated_results:
        return DataNotFoundException(detail=f"Item with ID {id} not found")
    return results


@router.get("/api/users/{orcid}/models", tags=["models"])
async def get_models_by_orcid(
    orcid: str = Path(
        ...,
        description="The ORCID of the user (e.g. 0000-0003-1813-6857)",
        examples=["0000-0003-1813-6857"],
    )
):
    """Returns model details based on an orcid."""
    mod_orcid = f"https://orcid.org/{orcid}"
    print(mod_orcid)
    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = (
        """
            PREFIX metago: <http://model.geneontology.org/>
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX has_affiliation: <http://purl.obolibrary.org/obo/ERO_0000066>
            PREFIX enabled_by: <http://purl.obolibrary.org/obo/RO_0002333>
            PREFIX BP: <http://purl.obolibrary.org/obo/GO_0008150>
            PREFIX MF: <http://purl.obolibrary.org/obo/GO_0003674>
            PREFIX CC: <http://purl.obolibrary.org/obo/GO_0005575>
            PREFIX biomacromolecule: <http://purl.obolibrary.org/obo/CHEBI_33694>

            SELECT distinct ?title ?contributor ?gocam
            WHERE {
                GRAPH ?gocam {
                                ?gocam metago:graphType metago:noctuaCam ;
                                dc:date ?date ;
                                dc:title ?title ;
                                dc:contributor ?contributor .


                                # Contributor filter
                                FILTER(?contributor = "%s")
                }
            }
            """
        % mod_orcid
    )

    results = si._sparql_query(query)

    if not results:
        raise DataNotFoundException(detail=f"Item with ID {orcid} not found")
    else:
        collated_results = []
        for result in results:
            collated_results.append({"model_id": result["gocam"].get("value"), "title": result["title"].get("value")})
        return collated_results


@router.get(
    "/api/models",
    tags=["models"],
    deprecated=True,
    description="Returns metadata of GO-CAM models, e.g. 59a6110e00000067.",
)
async def get_gocam_models(
    start: int = Query(None, description="start"),
    size: int = Query(None, description="Number of models to look for"),
    last: int = Query(None, description="last"),
    group: str = Query(None, description="group"),
    user: str = Query(None, description="user"),
    pmid: str = Query(None, description="pmid"),
    causalmf: bool = Query(
        False,
        description="The model has a chain of at least three functions connected "
        "by at least two consecutive causal relation edges.  One of these functions is enabled_by "
        "this input gene",
    ),
):
    """Returns metadata of GO-CAM models, e.g. 59a6110e00000067."""
    if last:
        start = 0
        size = last

    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)

    # support how the model endpoint currently works, better to have one param that controlled user group or pmid
    # since this is effectively is an OR at the moment.
    by_param = ""
    if group:
        by_param = group
    if user:
        by_param = user

    if by_param is not None:
        query = (
            """
            PREFIX metago: <http://model.geneontology.org/>
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX providedBy: <http://purl.org/pav/providedBy>

            SELECT  ?gocam ?date ?title (GROUP_CONCAT(distinct ?orcid; separator="@|@") AS ?orcids)
                                    (GROUP_CONCAT(distinct ?name; separator="@|@") AS ?names)
                                    (GROUP_CONCAT(distinct ?providedBy; separator="@|@") AS ?groupids)
                                    (GROUP_CONCAT(distinct ?providedByLabel; separator="@|@") AS ?groupnames)
            WHERE
            {
                {
                    BIND(" %s " as ?groupName) .
                    GRAPH ?gocam {
                        ?gocam metago:graphType metago:noctuaCam .
                        ?gocam dc:title ?title ;
                        dc:date ?date ;
                        dc:contributor ?orcid ;
                        providedBy: ?providedBy .

                    BIND( IRI(?orcid) AS ?orcidIRI ).
                    BIND( IRI(?providedBy) AS ?providedByIRI ).
                }

                optional {
                    ?providedByIRI rdfs:label ?providedByLabel .
                }

                filter(?providedByLabel = ?groupName )
                optional { ?orcidIRI rdfs:label ?name }
                BIND(IF(bound(?name), ?name, ?orcid) as ?name) .
            }

        }
        GROUP BY ?gocam ?date ?title
        ORDER BY DESC(?date)

        """
            % by_param
        )

    elif pmid is not None:
        if not pmid.startswith("PMID:"):
            pmid = "PMID:" + pmid
        query = (
            """

            PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX providedBy: <http://purl.org/pav/providedBy>

        SELECT  ?gocam ?date ?title (GROUP_CONCAT(distinct ?orcid; separator="@|@") AS ?orcids)
                                    (GROUP_CONCAT(distinct ?name; separator="@|@") AS ?names)
                                    (GROUP_CONCAT(distinct ?providedBy; separator="@|@") AS ?groupids)
                                    (GROUP_CONCAT(distinct ?providedByLabel; separator="@|@") AS ?groupnames)

        WHERE
        {
          GRAPH ?gocam {
            ?gocam metago:graphType metago:noctuaCam .

            ?gocam dc:title ?title ;
                   dc:date ?date ;
                   dc:contributor ?orcid ;
                   providedBy: ?providedBy .

            BIND( IRI(?orcid) AS ?orcidIRI ).
            BIND( IRI(?providedBy) AS ?providedByIRI ).

            ?s dc:source ?source .
            BIND(REPLACE(?source, " ", "") AS ?source) .
            FILTER(SAMETERM(?source, "%s"^^xsd:string))
          }

          optional {
            ?providedByIRI rdfs:label ?providedByLabel .
          }

          optional {
            ?orcidIRI rdfs:label ?name
          }
          BIND(IF(bound(?name), ?name, ?orcid) as ?name) .

        }
        GROUP BY ?gocam ?date ?title
        ORDER BY DESC(?date)

        """
            % pmid
        )

    elif causalmf is not None:
        query = """
        PREFIX pr: <http://purl.org/ontology/prv/core#>
        PREFIX metago: <http://model.geneontology.org/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX providedBy: <http://purl.org/pav/providedBy>

        PREFIX MF: <http://purl.obolibrary.org/obo/GO_0003674>

        PREFIX causally_upstream_of_or_within: <http://purl.obolibrary.org/obo/RO_0002418>
        PREFIX causally_upstream_of_or_within_negative_effect: <http://purl.obolibrary.org/obo/RO_0004046>
        PREFIX causally_upstream_of_or_within_positive_effect: <http://purl.obolibrary.org/obo/RO_0004047>

        PREFIX causally_upstream_of: <http://purl.obolibrary.org/obo/RO_0002411>
        PREFIX causally_upstream_of_negative_effect: <http://purl.obolibrary.org/obo/RO_0002305>
        PREFIX causally_upstream_of_positive_effect: <http://purl.obolibrary.org/obo/RO_0002304>

        PREFIX regulates: <http://purl.obolibrary.org/obo/RO_0002211>
        PREFIX negatively_regulates: <http://purl.obolibrary.org/obo/RO_0002212>
        PREFIX positively_regulates: <http://purl.obolibrary.org/obo/RO_0002213>

        PREFIX directly_regulates: <http://purl.obolibrary.org/obo/RO_0002578>
        PREFIX directly_positively_regulates: <http://purl.obolibrary.org/obo/RO_0002629>
        PREFIX directly_negatively_regulates: <http://purl.obolibrary.org/obo/RO_0002630>

        PREFIX directly_activates: <http://purl.obolibrary.org/obo/RO_0002406>
        PREFIX indirectly_activates: <http://purl.obolibrary.org/obo/RO_0002407>

        PREFIX directly_inhibits: <http://purl.obolibrary.org/obo/RO_0002408>
        PREFIX indirectly_inhibits: <http://purl.obolibrary.org/obo/RO_0002409>

        PREFIX transitively_provides_input_for: <http://purl.obolibrary.org/obo/RO_0002414>
        PREFIX immediately_causally_upstream_of: <http://purl.obolibrary.org/obo/RO_0002412>
        PREFIX directly_provides_input_for: <http://purl.obolibrary.org/obo/RO_0002413>

        SELECT  ?gocam ?date ?title (GROUP_CONCAT(distinct ?orcid; separator="@|@") AS ?orcids)
                                    (GROUP_CONCAT(distinct ?name; separator="@|@") AS ?names)
                                    (GROUP_CONCAT(distinct ?providedBy; separator="@|@") AS ?groupids)
                                    (GROUP_CONCAT(distinct ?providedByLabel; separator="@|@") AS ?groupnames)

        WHERE
        {
          ?causal1 rdfs:subPropertyOf* causally_upstream_of_or_within: .
          ?causal2 rdfs:subPropertyOf* causally_upstream_of_or_within: .
          {
            GRAPH ?gocam {
              ?gocam metago:graphType metago:noctuaCam .
              ?gocam dc:date ?date .
              ?gocam dc:title ?title .
              ?gocam dc:contributor ?orcid .
              ?gocam providedBy: ?providedBy .
              BIND( IRI(?orcid) AS ?orcidIRI ).
              BIND( IRI(?providedBy) AS ?providedByIRI ).
              ?ind1 ?causal1 ?ind2 .
              ?ind2 ?causal2 ?ind3
            }
            ?ind1 rdf:type MF: .
            ?ind2 rdf:type MF: .
            ?ind3 rdf:type MF: .
            optional {
                ?providedByIRI rdfs:label ?providedByLabel .
            }

            optional { ?orcidIRI rdfs:label ?name }
            BIND(IF(bound(?name), ?name, ?orcid) as ?name) .
          }
        }
        GROUP BY ?gocam ?date ?title
        ORDER BY ?gocam
        """
    else:
        query = """
            PREFIX metago: <http://model.geneontology.org/>
            PREFIX dc: <http://purl.org/dc/elements/1.1/>
            PREFIX providedBy: <http://purl.org/pav/providedBy>

            SELECT  ?gocam ?date ?title (GROUP_CONCAT(distinct ?orcid; separator="@|@") AS ?orcids)
                                    (GROUP_CONCAT(distinct ?name; separator="@|@") AS ?names)
                                    (GROUP_CONCAT(distinct ?providedBy; separator="@|@") AS ?groupids)
                                    (GROUP_CONCAT(distinct ?providedByLabel; separator="@|@") AS ?groupnames)
            WHERE
            {
                {
                    GRAPH ?gocam {
                        ?gocam metago:graphType metago:noctuaCam .
                        ?gocam dc:title ?title ;
                        dc:date ?date ;
                        dc:contributor ?orcid ;
                        providedBy: ?providedBy .

                        BIND( IRI(?orcid) AS ?orcidIRI ).
                        BIND( IRI(?providedBy) AS ?providedByIRI ).
                    }

                    optional {
                        ?providedByIRI rdfs:label ?providedByLabel .
                    }
                    optional { ?orcidIRI rdfs:label ?name }
                    BIND(IF(bound(?name), ?name, ?orcid) as ?name) .
                }

            }
            GROUP BY ?gocam ?date ?title
            ORDER BY DESC(?date)
        """
    if size:
        query += "\nLIMIT " + str(size)
    if start:
        query += "\nOFFSET " + str(start)
    results = si._sparql_query(query)
    transformed_results = transform_array(results, ["orcids", "names", "groupids", "groupnames"])
    logger.info(transformed_results)
    return transform_array(results, ["orcids", "names", "groupids", "groupnames"])
