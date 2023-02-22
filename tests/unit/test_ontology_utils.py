from fastapi.testclient import TestClient
from ontobio.sparql.sparql_ontology import EagerRemoteSparqlOntology

import app.utils.ontology.ontology_utils as ou
from app.main import app
from app.utils.settings import get_golr_config
test_client = TestClient(app)


def test_get_ontology_config():
    golr_url = get_golr_config()["solr_url"]["url"]
    assert "golr-aux.geneontology.io" in golr_url


def test_get_ontology():
    return_value = ou.get_ontology(id="go")
    assert type(return_value) is EagerRemoteSparqlOntology
    assert return_value.handle == "go"


def test_get_category_terms():
    category = {
        "description": "A location, relative to cellular compartments and structures, occupied by a macromolecular "
        "machine when it carries out a molecular function. There are two ways in which the "
        "gene ontology describes locations of gene products: (1) relative to cellular"
        " structures (e.g., cytoplasmic side of plasma membrane) or compartments "
        "(e.g., mitochondrion), and (2) the stable macromolecular complexes of "
        "which they are parts (e.g., the ribosome).",
        "groups": [
            {
                "id": "GO:0005575",
                "label": "all cellular component",
                "description": "Show all cellular component annotations",
                "type": "All",
            },
            {
                "description": "The space external to the outermost structure of a cell. "
                "For cells without external protective or external encapsulating "
                "structures this refers to space outside of the plasma membrane. This term "
                "covers the host cell environment outside an intracellular parasite.",
                "id": "GO:0005576",
                "label": "extracellular region",
                "type": "Term",
            },
            {
                "description": "The membrane surrounding a cell that separates the cell from its external "
                "environment. It consists of a phospholipid bilayer and associated proteins.",
                "id": "GO:0005886",
                "label": "plasma membrane",
                "type": "Term",
            },
            {
                "description": "The junction between an axon of one neuron and a dendrite of another "
                "neuron, a muscle fiber or a glial cell. As the axon approaches the synapse "
                "it enlarges into a specialized structure, the presynaptic terminal bouton, "
                "which contains mitochondria and synaptic vesicles. At the tip of the "
                "terminal bouton is the presynaptic membrane; facing it, and separated "
                "from it by a minute cleft (the synaptic cleft) is a specialized area of "
                "membrane on the receiving cell, known as the postsynaptic membrane. In "
                "response to the arrival of nerve impulses, the presynaptic terminal bouton "
                "secretes molecules of neurotransmitters into the synaptic cleft. These "
                "diffuse across the cleft and transmit the signal to the postsynaptic "
                "membrane.",
                "id": "GO:0045202",
                "label": "synapse",
                "type": "Term",
            },
            {
                "description": "A cellular component that forms a specialized region of connection between "
                "two or more cells, or between a cell and the extracellular matrix, or "
                "between two membrane-bound components of a cell, such as flagella.",
                "id": "GO:0030054",
                "label": "cell junction",
                "type": "Term",
            },
            {
                "description": "A prolongation or process extending from a cell, e.g. a flagellum or axon.",
                "id": "GO:0042995",
                "label": "cell projection",
                "type": "Term",
            },
            {
                "description": "A vesicle found in the cytoplasm of a cell.",
                "id": "GO:0031410",
                "label": "cytoplasmic vesicle",
                "type": "Term",
            },
            {
                "description": "A vacuole to which materials ingested by endocytosis are delivered.",
                "id": "GO:0005768",
                "label": "endosome",
                "type": "Term",
            },
            {
                "description": "A closed structure, found only in eukaryotic cells, that is completely "
                "surrounded by unit membrane and contains liquid material. Cells contain"
                " one or several vacuoles, that may have different functions from each "
                "other. Vacuoles have a diverse array of functions. They can act as a "
                "storage organelle for nutrients or waste products, as a degradative "
                "compartment, as a cost-effective way of increasing cell size, and as a "
                "homeostatic regulator controlling both turgor pressure and pH of the "
                "cytosol.",
                "id": "GO:0005773",
                "label": "vacuole",
                "type": "Term",
            },
            {
                "description": "A membrane-bound cytoplasmic organelle of the endomembrane system "
                "that further processes the core oligosaccharides (e.g. N-glycans) "
                "added to proteins in the endoplasmic reticulum and packages them into "
                "membrane-bound vesicles. The Golgi apparatus operates at the intersection "
                "of the secretory, lysosomal, and endocytic pathways.",
                "id": "GO:0005794",
                "label": "Golgi apparatus",
                "type": "Term",
            },
            {
                "description": "The irregular network of unit membranes, visible only by electron "
                "microscopy, that occurs in the cytoplasm of many eukaryotic cells. The "
                "membranes form a complex meshwork of tubular channels, which are often "
                "expanded into slitlike"
                " cavities called cisternae. The ER takes two forms, rough (or granular), "
                "with ribosomes adhering to the outer surface, and smooth (with no "
                "ribosomes attached).",
                "id": "GO:0005783",
                "label": "endoplasmic reticulum",
                "type": "Term",
            },
            {
                "description": "The part of the cytoplasm that does not contain organelles but which does "
                "contain other particulate matter, such as protein complexes.",
                "id": "GO:0005829",
                "label": "cytosol",
                "type": "Term",
            },
            {
                "description": "A semiautonomous, self replicating organelle that occurs in varying numbers,"
                " shapes, and sizes in the cytoplasm of virtually all eukaryotic cells. It "
                "is notably the site of tissue respiration.",
                "id": "GO:0005739",
                "label": "mitochondrion",
                "type": "Term",
            },
            {
                "description": "A membrane-bounded organelle of eukaryotic cells in which chromosomes are "
                "housed and replicated. In most cells, the nucleus contains all of the cell's"
                " chromosomes except the organellar chromosomes, and is the site of RNA "
                "synthesis and processing. In some species, or in specialized cell types, "
                "RNA metabolism or DNA replication may be absent.",
                "id": "GO:0005634",
                "label": "nucleus",
                "type": "Term",
            },
            {
                "description": "A structure composed of a very long molecule of DNA and associated "
                "proteins (e.g. histones) that carries hereditary information.",
                "id": "GO:0005694",
                "label": "chromosome",
                "type": "Term",
            },
            {
                "description": "Any of the various filamentous elements that form the internal framework "
                "of cells, and typically remain after treatment of the cells with mild "
                "detergent to remove membrane constituents and soluble components of the "
                "cytoplasm. The term embraces intermediate filaments, microfilaments, "
                "microtubules, the microtrabecular lattice, and other structures "
                "characterized by a polymeric filamentous nature and long-range order within "
                "the cell. The various elements of the cytoskeleton not only serve in the "
                "maintenance of cellular shape but also have roles in other cellular "
                "functions, including cellular movement, cell division, endocytosis, "
                "and movement of organelles.",
                "id": "GO:0005856",
                "label": "cytoskeleton",
                "type": "Term",
            },
            {
                "description": "A stable assembly of two or more macromolecules, i.e. proteins, "
                "nucleic acids, carbohydrates or lipids, in which at least one "
                "component is a protein and the constituent parts function together.",
                "id": "GO:0032991",
                "label": "protein-containing complex",
                "type": "Term",
            },
            {
                "id": "GO:0005575",
                "label": "other cellular component",
                "description": "Represent all annotations not mapped to a specific term",
                "type": "Other",
            },
        ],
        "id": "GO:0005575",
        "label": "cellular_component",
    }

    return_value = ou.get_category_terms(category)
    assert len(return_value) == 16
    terms = []
    for term in return_value:
        terms.append(term.get("id"))
    assert "GO:0005783" in terms


def test_get_ontology_subsets_by_id():
    ribbon_categories = ou.get_ontology_subsets_by_id("goslim_agr")
    assert len(ribbon_categories) == 3
    for ribbon_category in ribbon_categories:
        if ribbon_category.get("annotation_class") == "GO:0003674":
            assert len(ribbon_category.get("terms")) == 16


def test_correct_goid():
    corrected_id = ou.correct_goid(goid="GO:00012345")
    assert corrected_id == "GO_00012345"


def test_get_go_subsets():
    subset_sparql = ou.get_go_subsets_sparql_query(goid="GO:0003674")
    assert subset_sparql is not None
    assert "GO_0003674" in subset_sparql


def test_create_go_summary_sparql():
    go_summary_sparql = ou.create_go_summary_sparql(goid="GO:0003674")
    assert go_summary_sparql is not None
    assert "GO_0003674" in go_summary_sparql
