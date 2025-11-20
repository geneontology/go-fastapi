"""Utilities for MyGene.info interactions."""

import logging

from biothings_client import get_client

from app.exceptions.global_exceptions import DataNotFoundException

logger = logging.getLogger()


def gene_to_uniprot_from_mygene(id: str):
    """Query MyGeneInfo with a gene and get its corresponding UniProt ID."""
    uniprot_ids = []
    mg = get_client("gene")
    if id.startswith("NCBIGene:"):
        # MyGeneInfo uses 'entrezgene' prefix instead of 'NCBIGene'
        id = id.replace("NCBIGene", "entrezgene")
    try:
        results = mg.query(id, fields="uniprot")
        logger.info("results from mygene for %s: %s", id, results["hits"])
        if results["hits"]:
            for hit in results["hits"]:
                if "uniprot" not in hit:
                    continue
                if "Swiss-Prot" in hit["uniprot"]:
                    uniprot_id = hit["uniprot"]["Swiss-Prot"]
                    if isinstance(uniprot_id, str):
                        if not uniprot_id.startswith("UniProtKB"):
                            uniprot_id = "UniProtKB:{}".format(uniprot_id)
                        uniprot_ids.append(uniprot_id)
                    else:
                        for x in uniprot_id:
                            if not x.startswith("UniProtKB"):
                                x = "UniProtKB:{}".format(x)
                            uniprot_ids.append(x)
                else:
                    trembl_ids = hit["uniprot"]["TrEMBL"]
                    for x in trembl_ids:
                        if not x.startswith("UniProtKB"):
                            x = "UniProtKB:{}".format(x)
                        uniprot_ids.append(x)
    except ConnectionError:
        logging.error("ConnectionError while querying MyGeneInfo with {}".format(id))
    if not uniprot_ids:
        raise DataNotFoundException(detail="No UniProtKB IDs found for {}".format(id))
    return uniprot_ids


def uniprot_to_gene_from_mygene(id: str):
    """Query MyGeneInfo with a UniProtKB id and get its corresponding HGNC gene."""
    gene_id = None
    if id.startswith("UniProtKB"):
        id = id.split(":", 1)[1]

    mg = get_client("gene")
    try:
        # Query specifically in the uniprot fields to avoid false matches
        results = mg.query(f"uniprot.Swiss-Prot:{id} OR uniprot.TrEMBL:{id}",
                          fields="HGNC,symbol,uniprot")
        if results["hits"]:
            # Verify the hit actually contains our UniProt ID
            for hit in results["hits"]:
                if "uniprot" in hit:
                    uniprot_data = hit["uniprot"]
                    # Check Swiss-Prot
                    has_id = False
                    if "Swiss-Prot" in uniprot_data:
                        swiss_prot = uniprot_data["Swiss-Prot"]
                        if (isinstance(swiss_prot, str) and swiss_prot == id) or \
                           (isinstance(swiss_prot, list) and id in swiss_prot):
                            has_id = True
                    # Check TrEMBL if not found
                    if not has_id and "TrEMBL" in uniprot_data:
                        trembl = uniprot_data["TrEMBL"]
                        if (isinstance(trembl, str) and trembl == id) or \
                           (isinstance(trembl, list) and id in trembl):
                            has_id = True

                    if has_id and "HGNC" in hit:
                        gene_id = hit["HGNC"]
                        if not gene_id.startswith("HGNC"):
                            gene_id = "HGNC:{}".format(gene_id)
                        break
    except ConnectionError:
        logging.error("ConnectionError while querying MyGeneInfo with {}".format(id))

    if not gene_id:
        raise DataNotFoundException(detail="No HGNC IDs found for {}".format(id))
    return [gene_id]
