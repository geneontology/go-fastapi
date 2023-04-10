import logging
from typing import List
from fastapi import APIRouter, Query
from oaklib.implementations.sparql.sparql_implementation import SparqlImplementation
from oaklib.resource import OntologyResource
from ontobio.golr.golr_query import ESOLR, replace
import app.utils.ontology.ontology_utils as ontology_utils
from app.utils.golr.golr_utils import run_solr_text_on
from app.utils.settings import (ESOLR, ESOLRDoc, get_sparql_endpoint,
                                get_user_agent)
from app.utils.sparql.sparql_utils import transform_array

from .slimmer import gene_to_uniprot_from_mygene

log = logging.getLogger(__name__)

USER_AGENT = get_user_agent()
router = APIRouter()

aspect_map = {"P": "GO:0008150", "F": "GO:0003674", "C": "GO:0005575"}


@router.get("/api/ontology/term/{id}/subsets", tags=["ontology"])
async def get_ontology_subsets_by_go_term_id(
    id: str = Query(
        None, description="'CURIE identifier of a GO term," " e.g. GO:0006259"
    )
):
    """
    Returns subsets (slims) associated to an ontology term
    """
    query = ontology_utils.get_go_subsets_sparql_query(id)
    # replace with OntologyFactory with ontobio - but config on startup
    # or use OAK  here and rewrite - still need to config on startup (SQLLite - up front to make
    # the latest version, etc.)

    ont_r = OntologyResource(url=get_sparql_endpoint())
    si = SparqlImplementation(ont_r)
    query = ontology_utils.create_go_summary_sparql(id)
    results = si._sparql_query(query)
    results = transform_array(results, [])
    results = replace(results, "subset", "OBO:go#", "")
    return results


@router.get("/api/ontology/subset/{id}", tags=["ontology"])
async def get_subset_by_id(id: str):
    result = ontology_utils.get_ontology_subsets_by_id(id=id)
    return result


@router.get("/api/ontology/ribbon/", tags=["ontology"])
async def get_ribbon_results(
    subset: str = Query(
        None, description="Name of the subset to map GO terms " "(e.g. goslim_agr)"
    ),
    subject: List[str] = Query(
        None, description="List of Gene ids (e.g. " "MGI:98214, RGD:620474)"
    ),
    ecodes: List[str] = Query(
        None,
        description="List of Evidence Codes to include (e.g. "
        "EXP, IDA). Has priority over exclude_IBA",
    ),
    exclude_IBA: bool = Query(False, description="If true, excludes IBA annotations"),
    exclude_PB: bool = Query(
        False, description="If true, excludes direct annotations to protein binding"
    ),
    cross_aspect: bool = Query(
        False,
        description="If true, can retrieve terms from "
        "other aspects if using a "
        "cross-aspect"
        " relationship such as "
        "regulates_closure",
    ),
):
    """
    Fetch the summary of annotations for a given gene or set of genes
    """

    # Step 1: create the categories
    categories = ontology_utils.get_ontology_subsets_by_id(subset)
    for category in categories:
        category["groups"] = category["terms"]
        del category["terms"]

        category["id"] = category["annotation_class"]
        del category["annotation_class"]

        category["label"] = category["annotation_class_label"]
        del category["annotation_class_label"]

        for group in category["groups"]:
            group["id"] = group["annotation_class"]
            del group["annotation_class"]

            group["label"] = group["annotation_class_label"]
            del group["annotation_class_label"]

            group["type"] = "Term"

        category["groups"] = (
            [
                {
                    "id": category["id"],
                    "label": "all " + category["label"].lower().replace("_", " "),
                    "description": "Show all "
                    + category["label"].lower().replace("_", " ")
                    + " annotations",
                    "type": "All",
                }
            ]
            + category["groups"]
            + [
                {
                    "id": category["id"],
                    "label": "other " + category["label"].lower().replace("_", " "),
                    "description": "Represent all annotations not "
                    "mapped to a specific term",
                    "type": "Other",
                }
            ]
        )

    # Step 2: create the entities / subjects
    subject_ids = subject

    # ID conversion
    subject_ids = [
        x.replace("WormBase:", "WB:") if "WormBase:" in x else x for x in subject_ids
    ]
    slimmer_subjects = []
    mapped_ids = {}
    reverse_mapped_ids = {}
    for s in subject_ids:
        if "HGNC:" in s or "NCBIGene:" in s or "ENSEMBL:" in s:
            prots = gene_to_uniprot_from_mygene(s)
            if len(prots) > 0:
                mapped_ids[s] = prots[0]
                reverse_mapped_ids[prots[0]] = s
                if len(prots) == 0:
                    prots = [s]
                slimmer_subjects += prots
        else:
            slimmer_subjects.append(s)

    log.info("SLIMMER SUBS : ", slimmer_subjects)
    subject_ids = slimmer_subjects

    # should remove any undefined subject
    for subject_id in subject_ids:
        if subject_id == "undefined":
            subject_ids.remove(subject_id)

    # because of the MGI:MGI
    mod_ids = []

    subjects = []
    for subject_id in subject_ids:
        entity = {
            "id": subject_id,
            "groups": {},
            "nb_classes": 0,
            "nb_annotations": 0,
            "terms": set(),
        }

        if subject_id.startswith("MGI:"):
            subject_id = "MGI:" + subject_id
        mod_ids.append(subject_id)

        q = "*:*"
        qf = ""
        fq = '&fq=bioentity:"' + subject_id + '"&rows=100000'
        fields = "annotation_class,evidence_type,regulates_closure,aspect"
        if ecodes:
            fq += '&fq=evidence_type:("' + '" "'.join(ecodes) + '")'
        elif exclude_IBA:
            fq += "&fq=!evidence_type:IBA"
        if exclude_PB:
            fq += '&fq=!annotation_class:"GO:0005515"'
        log.info(fq)

        data = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.ANNOTATION, q, qf, fields, fq)

        # compute number of terms and annotations
        for annot in data:
            aspect = ontology_utils.aspect_map[annot["aspect"]]
            found = False

            for cat in categories:
                for gp in cat["groups"]:
                    group = gp["id"]

                    if gp["type"] == "Other":
                        continue

                    # only allow annotated terms belonging to the same category if cross_aspect
                    if cross_aspect or cat["id"] == aspect:
                        # is this annotation part of the current group, based on the regulates_closure ?
                        if group in annot["regulates_closure"]:
                            found = True
                            break
            if found:
                entity["terms"].add(annot["annotation_class"])
                entity["nb_annotations"] += 1

        for cat in categories:
            for gp in cat["groups"]:
                group = gp["id"]

                if gp["type"] == "Other":
                    continue

                for annot in data:
                    aspect = ontology_utils.aspect_map[annot["aspect"]]

                    # only allow annotated terms belonging to the same category if cross_aspect
                    if cross_aspect or cat["id"] == aspect:
                        # is this annotation part of the current group, based on the regulates_closure ?
                        if group in annot["regulates_closure"]:
                            # if the group has not been met yet, create it
                            if group not in entity["groups"]:
                                entity["groups"][group] = {}
                                entity["groups"][group]["ALL"] = {
                                    "terms": set(),
                                    "nb_classes": 0,
                                    "nb_annotations": 0,
                                }

                            # if the subgroup has not been met yet, create it
                            if annot["evidence_type"] not in entity["groups"][group]:
                                entity["groups"][group][annot["evidence_type"]] = {
                                    "terms": set(),
                                    "nb_classes": 0,
                                    "nb_annotations": 0,
                                }

                            # for each annotation, add the term and increment the nb of annotations
                            entity["groups"][group][annot["evidence_type"]][
                                "terms"
                            ].add(annot["annotation_class"])
                            entity["groups"][group][annot["evidence_type"]][
                                "nb_annotations"
                            ] += 1
                            entity["groups"][group]["ALL"]["terms"].add(
                                annot["annotation_class"]
                            )
                            entity["groups"][group]["ALL"]["nb_annotations"] += 1

            terms = ontology_utils.get_category_terms(cat)
            terms = [term["id"] for term in terms]

            other = {"ALL": {"terms": set(), "nb_classes": 0, "nb_annotations": 0}}

            for annot in data:
                aspect = ontology_utils.aspect_map[annot["aspect"]]

                # only allow annotated terms belonging to the same category if cross_aspect
                if cross_aspect or cat["id"] == aspect:
                    found = False
                    for term in terms:
                        if term in annot["regulates_closure"]:
                            found = True
                            break

                    if not found:
                        other["ALL"]["nb_annotations"] += 1
                        other["ALL"]["terms"].add(annot["annotation_class"])
                        if annot["evidence_type"] not in other:
                            other[annot["evidence_type"]] = {
                                "terms": set(),
                                "nb_classes": 0,
                                "nb_annotations": 0,
                            }
                        other[annot["evidence_type"]]["nb_annotations"] += 1
                        other[annot["evidence_type"]]["terms"].add(
                            annot["annotation_class"]
                        )

            entity["groups"][cat["id"] + "-other"] = other

        # compute the number of classes for each group that have subgroup (annotations)
        for group in entity["groups"]:
            for subgroup in entity["groups"][group]:
                entity["groups"][group][subgroup]["nb_classes"] = len(
                    entity["groups"][group][subgroup]["terms"]
                )
                if "-other" not in group:
                    del entity["groups"][group][subgroup]["terms"]
                else:
                    entity["groups"][group][subgroup]["terms"] = list(
                        entity["groups"][group][subgroup]["terms"]
                    )

        entity["nb_classes"] = len(entity["terms"])
        del entity["terms"]

        subjects.append(entity)

    # fill out the entity details
    q = "*:*"
    qf = ""
    fq = '&fq=bioentity:("' + '" or "'.join(mod_ids) + '")&rows=100000'
    fields = "bioentity,bioentity_label,taxon,taxon_label"
    data = run_solr_text_on(ESOLR.GOLR, ESOLRDoc.BIOENTITY, q, qf, fields, fq)

    for entity in subjects:
        for entity_detail in data:
            subject_id = entity_detail["bioentity"].replace("MGI:MGI:", "MGI:")

            if entity["id"] == subject_id:
                entity["label"] = entity_detail["bioentity_label"]
                entity["taxon_id"] = entity_detail["taxon"]
                entity["taxon_label"] = entity_detail["taxon_label"]

    # map the entity back to their original IDs
    for entity in subjects:
        if entity["id"] in reverse_mapped_ids:
            entity["id"] = reverse_mapped_ids[entity["id"]]

            # if any subject without annotation is retrieved, remove it
    to_remove = []
    for entity in subjects:
        if entity["nb_annotations"] == 0:
            to_remove.append(entity)

    for entity in to_remove:
        subjects.remove(entity)

    # http://golr-aux.geneontology.io/solr/select/?q=*:*&fq=document_category:%22bioentity%22&rows=10&wt=json&fl=bioentity,bioentity_label,taxon,taxon_label&fq=bioentity:(%22MGI:MGI:98214%22%20or%20%22RGD:620474%22)

    result = {"categories": categories, "subjects": subjects}
    return result
