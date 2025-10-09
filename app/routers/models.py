"""Model API router."""

import logging
from pprint import pprint
from typing import List

import requests
from fastapi import APIRouter, Path, Query
from gocam.translation.minerva_wrapper import MinervaWrapper

from app.exceptions.global_exceptions import DataNotFoundException, InvalidIdentifier
from app.utils import ontology_utils
from app.utils.settings import get_user_agent

USER_AGENT = get_user_agent()
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
        example="581e072c00000295",
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
        example=["581e072c00000295", "SYNGO_369"],
    )
):
    """Returns go term details based on a GO-CAM model ID."""
    GO_ROOTS = {
        "http://purl.obolibrary.org/obo/GO_0008150": "BP",
        "http://purl.obolibrary.org/obo/GO_0003674": "MF",
        "http://purl.obolibrary.org/obo/GO_0005575": "CC",
    }

    collated_results = []

    for model_id in gocams:
        go_terms = {}

        model_data = await get_model_details_by_model_id_json(model_id)
        gocam_id = model_data.get("id", "")

        for individual in model_data.get("individuals", []):
            for type_item in individual.get("type", []):
                go_id = type_item.get("id", "")

                if go_id.startswith("GO:"):
                    go_iri = f"http://purl.obolibrary.org/obo/{go_id.replace(':', '_')}"

                    if go_iri not in GO_ROOTS and go_id not in go_terms:
                        root_type = individual.get("root-type", [])
                        go_class = "unknown"
                        for root in root_type:
                            root_id = root.get("id", "")
                            if root_id.startswith("GO:"):
                                root_iri = f"http://purl.obolibrary.org/obo/{root_id.replace(':', '_')}"
                                if root_iri in GO_ROOTS:
                                    go_class = GO_ROOTS[root_iri]
                                    break

                        go_terms[go_id] = {
                            "goid": go_iri,
                            "goname": type_item.get("label", ""),
                            "goclass": go_class,
                        }

        if go_terms:
            collated_results.append({
                "gocam": gocam_id,
                "goclasses": [term["goclass"] for term in go_terms.values()],
                "goids": [term["goid"] for term in go_terms.values()],
                "gonames": [term["goname"] for term in go_terms.values()],
            })

    if not collated_results:
        raise DataNotFoundException("GO-CAM model not found.")

    return collated_results


@router.get("/api/models/gp", tags=["models"], description="Returns gene product details based on a GO-CAM model ID.")
async def get_geneproducts_by_model_id(
    gocams: List[str] = Query(
        None,
        description="A list of GO-CAM IDs separated by a comma, e.g. 59a6110e00000067,SYNGO_369",
        example=["581e072c00000295", "SYNGO_369"],
    )
):
    """
    Returns gene product details based on a GO-CAM model ID.

    :param gocams: A list of GO-CAM IDs separated by a comma, e.g. 59a6110e00000067,SYNGO_369
    :return: gene product details based on a GO-CAM model ID.
    """
    EXCLUDED_PREFIXES = ("GO:", "ECO:", "CHEBI:", "gomodel:")

    collated_results = []

    for model_id in gocams:
        model_data = await get_model_details_by_model_id_json(model_id)
        gocam_id = model_data.get("id", "")

        individual_map = {}
        for ind in model_data.get("individuals", []):
            ind_id = ind.get("id", "")
            for type_item in ind.get("type", []):
                gp_id = type_item.get("id", "")
                gp_label = type_item.get("label", "")
                if gp_id and not any(gp_id.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
                    if ind_id not in individual_map:
                        individual_map[ind_id] = []
                    individual_map[ind_id].append({"id": gp_id, "label": gp_label})

        gene_products = {}
        for fact in model_data.get("facts", []):
            if fact.get("property") == "RO:0002333":
                obj_id = fact.get("object", "")
                if obj_id in individual_map:
                    for gp in individual_map[obj_id]:
                        gp_id = gp["id"]
                        if gp_id not in gene_products:
                            gene_products[gp_id] = gp["label"]

        if gene_products:
            gpids = "@|@".join(gene_products.keys())
            gpnames = "@|@".join(gene_products.values())
            collated_results.append({
                "gocam": gocam_id,
                "gpids": gpids,
                "gpnames": gpnames,
            })

    if not collated_results:
        raise DataNotFoundException("GO-CAM model not found.")

    return collated_results


@router.get("/api/models/pmid", tags=["models"], description="Returns PMID details based on a GO CAM ID.")
async def get_pmid_by_model_id(
    gocams: List[str] = Query(
        None,
        description="A list of GO-CAM IDs separated by a comma, e.g. 59a6110e00000067,SYNGO_369",
        example=["581e072c00000295", "SYNGO_369"],
    )
):
    """Returns pubmed details based on a GO CAM id."""
    import re

    collated_results = []

    for model_id in gocams:
        pmids = set()

        model_data = await get_model_details_by_model_id_json(model_id)
        gocam_id = model_data.get("id", "")

        for ann in model_data.get("annotations", []):
            value = ann.get("value", "")
            if "PMID" in value:
                matches = re.findall(r"PMID:\s*\d+", value)
                for match in matches:
                    pmids.add(match.replace(" ", ""))

        for ind in model_data.get("individuals", []):
            for ann in ind.get("annotations", []):
                if ann.get("key", "") == "source":
                    value = ann.get("value", "")
                    if "PMID" in value:
                        matches = re.findall(r"PMID:\s*\d+", value)
                        for match in matches:
                            pmids.add(match.replace(" ", ""))

        for fact in model_data.get("facts", []):
            for ann in fact.get("annotations", []):
                if ann.get("key", "") == "source":
                    value = ann.get("value", "")
                    if "PMID" in value:
                        matches = re.findall(r"PMID:\s*\d+", value)
                        for match in matches:
                            pmids.add(match.replace(" ", ""))

        if pmids:
            sources = "@|@".join(sorted(pmids))
            collated_results.append({"gocam": gocam_id, "sources": sources})

    if not collated_results:
        raise DataNotFoundException("GO-CAM model not found.")

    return collated_results


@router.get(
    "/api/go-cam/{id}", tags=["models"], description="Returns model details based on a GO-CAM model ID in JSON format."
)  # note: this is the endpoint that is currently used by gocam-py to for use in CTX export.
async def get_model_details_by_model_id_json(
    id: str = Path(
        ...,
        description="A GO-CAM identifier (e.g. 581e072c00000820, 581e072c00000295, 5900dc7400000968)",
        example="gomodel:66187e4700001573",
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
        example="581e072c00000295",
    )
):
    """Returns model details based on a GO-CAM model ID."""
    model_data = await get_model_details_by_model_id_json(id)

    collated_results = []

    model_id = model_data.get("id", "")

    for ind in model_data.get("individuals", []):
        ind_id = ind.get("id", "")

        for type_item in ind.get("type", []):
            collated_results.append({
                "subject": ind_id,
                "predicate": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
                "object": type_item.get("id", ""),
            })

        for ann in ind.get("annotations", []):
            key = ann.get("key", "")
            value = ann.get("value", "")
            if key == "contributor":
                predicate = "http://purl.org/dc/elements/1.1/contributor"
            elif key == "date":
                predicate = "http://purl.org/dc/elements/1.1/date"
            elif key == "source":
                predicate = "http://purl.org/dc/elements/1.1/source"
            elif key == "providedBy":
                predicate = "http://purl.org/pav/providedBy"
            elif key == "with":
                predicate = "http://geneontology.org/lego/evidence-with"
            else:
                predicate = f"http://geneontology.org/lego/{key}"

            collated_results.append({
                "subject": ind_id,
                "predicate": predicate,
                "object": value,
            })

    for fact in model_data.get("facts", []):
        subject = fact.get("subject", "")
        prop = fact.get("property", "")
        obj = fact.get("object", "")

        if prop:
            prop_iri = f"http://purl.obolibrary.org/obo/{prop.replace(':', '_')}" if ":" in prop else prop
            collated_results.append({
                "subject": subject,
                "predicate": prop_iri,
                "object": obj,
            })

        for ann in fact.get("annotations", []):
            key = ann.get("key", "")
            value = ann.get("value", "")
            fact_id = f"{subject}-{prop}-{obj}"

            if key == "contributor":
                predicate = "http://purl.org/dc/elements/1.1/contributor"
            elif key == "date":
                predicate = "http://purl.org/dc/elements/1.1/date"
            elif key == "source":
                predicate = "http://purl.org/dc/elements/1.1/source"
            elif key == "providedBy":
                predicate = "http://purl.org/pav/providedBy"
            else:
                predicate = f"http://geneontology.org/lego/{key}"

            collated_results.append({
                "subject": fact_id,
                "predicate": predicate,
                "object": value,
            })

    for ann in model_data.get("annotations", []):
        key = ann.get("key", "")
        value = ann.get("value", "")

        if key == "title":
            predicate = "http://purl.org/dc/elements/1.1/title"
        elif key == "contributor":
            predicate = "http://purl.org/dc/elements/1.1/contributor"
        elif key == "date":
            predicate = "http://purl.org/dc/elements/1.1/date"
        elif key == "providedBy":
            predicate = "http://purl.org/pav/providedBy"
        elif key == "state":
            predicate = "http://geneontology.org/lego/modelstate"
        else:
            predicate = f"http://geneontology.org/lego/{key}"

        collated_results.append({
            "subject": model_id,
            "predicate": predicate,
            "object": value,
        })

    return collated_results


@router.get("/api/taxon/{taxon}/models", tags=["models"], description="Returns model details based on a NCBI Taxon ID.")
async def get_term_details_by_taxon_id(
    taxon: str = Path(
        ...,
        description="A taxon identifier (e.g. NCBITaxon:9606, NCBITaxon:10090, NCBITaxon:10116)",
        example="NCBITaxon:9606",
    )
):
    """Returns model details based on a NCBI Taxon ID."""
    from app.utils.settings import get_index_files

    taxon_index = get_index_files("gocam_taxon_index_file")

    if taxon not in taxon_index:
        # Only validate with Golr if not found in index
        # This allows tests to work without external Golr dependency
        try:
            ontology_utils.is_golr_recognized_curie(taxon)
        except DataNotFoundException as e:
            raise DataNotFoundException(detail=str(e)) from e
        except ValueError as e:
            raise InvalidIdentifier(detail=str(e)) from e
        except Exception:
            # If Golr is unavailable and taxon not in index, return empty
            return []
        return []

    model_ids = taxon_index[taxon]
    collated_results = []
    for model_id in model_ids:
        gocam_iri = f"http://model.geneontology.org/{model_id}"
        collated_results.append({"gocam": gocam_iri})

    return collated_results


@router.get(
    "/api/pmid/{id}/models",
    tags=["models"],
    description="Returns models for a given publication identifier (PMID).",
)
async def get_model_details_by_pmid(
    id: str = Path(..., description="A publication identifier (PMID) (e.g. 15314168 or 26954676)")
):
    """Returns models for a given publication identifier (PMID)."""
    from app.utils.settings import get_index_files

    pmid_key = id if id.startswith("PMID:") else f"PMID:{id}"

    source_index = get_index_files("gocam_source_index_file")

    if pmid_key not in source_index:
        raise DataNotFoundException(detail=f"Item with ID {id} not found")

    model_ids = source_index[pmid_key]
    collated_results = []
    for model_id in model_ids:
        gocam_iri = f"http://model.geneontology.org/{model_id}"
        collated_results.append({"gocam": gocam_iri})

    return collated_results
