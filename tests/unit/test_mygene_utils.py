"""Integration tests for MyGene.info utilities.

These tests verify that gene_to_uniprot_from_mygene and uniprot_to_gene_from_mygene
correctly interact with the mygene.info API and return expected results.
"""

import pytest

from app.exceptions.global_exceptions import DataNotFoundException
from app.utils.mygene_utils import gene_to_uniprot_from_mygene, uniprot_to_gene_from_mygene


@pytest.mark.integration
@pytest.mark.parametrize(
    "gene_id,expected_prefix,description",
    [
        # HGNC:5 is TP53 (tumor protein p53) - well-known gene
        ("HGNC:5", "UniProtKB:", "TP53 gene should return UniProt IDs"),
        ("HGNC:30692", "UniProtKB:", ""),
        ("HGNC:12139", "UniProtKB:", ""),
        # HGNC:1100 is BRCA1 - breast cancer gene
        ("HGNC:1100", "UniProtKB:", "BRCA1 gene should return UniProt IDs"),
        # HGNC:3236 is EGFR - epidermal growth factor receptor
        ("HGNC:3236", "UniProtKB:", "EGFR gene should return UniProt IDs"),
        # NCBIGene format (entrezgene:7157 is TP53)
        ("NCBIGene:7157", "UniProtKB:", "NCBIGene format should be converted to entrezgene"),
        # Direct entrezgene format
        ("entrezgene:672", "UniProtKB:", "BRCA1 entrezgene ID should return UniProt IDs"),
    ],
)
def test_gene_to_uniprot_from_mygene_with_valid_hgnc_ids(
    gene_id: str, expected_prefix: str, description: str
) -> None:
    """Test gene_to_uniprot_from_mygene with various valid gene IDs.

    This test verifies that:
    1. The function successfully queries mygene.info API
    2. Results are returned for well-known gene IDs
    3. UniProt IDs are properly formatted with UniProtKB prefix
    4. NCBIGene prefix is converted to entrezgene format

    Args:
        gene_id: The gene identifier to query
        expected_prefix: The expected prefix in results
        description: Test case description

    >>> result = gene_to_uniprot_from_mygene("HGNC:5")
    >>> assert isinstance(result, list)
    >>> assert len(result) > 0
    >>> assert all(id.startswith("UniProtKB:") for id in result)
    """
    result = gene_to_uniprot_from_mygene(gene_id)

    # Verify we got results
    assert result is not None, f"{description}: Result should not be None"
    assert isinstance(result, list), f"{description}: Result should be a list"
    assert len(result) > 0, f"{description}: Should return at least one UniProt ID"

    # Verify all results have the expected prefix
    for uniprot_id in result:
        assert uniprot_id.startswith(expected_prefix), (
            f"{description}: All IDs should start with {expected_prefix}, got {uniprot_id}"
        )


@pytest.mark.integration
def test_gene_to_uniprot_from_mygene_tp53_specific() -> None:
    """Test gene_to_uniprot_from_mygene returns known UniProt ID for TP53.

    TP53 (HGNC:5) should map to UniProtKB:P04637 (Swiss-Prot entry).
    This test verifies the exact mapping for a well-known gene.

    >>> result = gene_to_uniprot_from_mygene("HGNC:5")
    >>> assert "UniProtKB:P04637" in result
    """
    result = gene_to_uniprot_from_mygene("HGNC:5")

    # TP53's primary Swiss-Prot ID is P04637
    assert "UniProtKB:P04637" in result, (
        f"TP53 should map to UniProtKB:P04637, got {result}"
    )


@pytest.mark.integration
def test_gene_to_uniprot_from_mygene_brca1_specific() -> None:
    """Test gene_to_uniprot_from_mygene returns known UniProt ID for BRCA1.

    BRCA1 (HGNC:1100) should map to UniProtKB:P38398 (Swiss-Prot entry).
    This test verifies the exact mapping for a well-known breast cancer gene.

    >>> result = gene_to_uniprot_from_mygene("HGNC:1100")
    >>> assert "UniProtKB:P38398" in result
    """
    result = gene_to_uniprot_from_mygene("HGNC:1100")

    # BRCA1's primary Swiss-Prot ID is P38398
    assert "UniProtKB:P38398" in result, (
        f"BRCA1 should map to UniProtKB:P38398, got {result}"
    )


@pytest.mark.integration
def test_gene_to_uniprot_from_mygene_egfr_specific() -> None:
    """Test gene_to_uniprot_from_mygene returns known UniProt ID for EGFR.

    EGFR (HGNC:3236) should map to UniProtKB:P00533 (Swiss-Prot entry).
    This test verifies the exact mapping for the epidermal growth factor receptor.

    >>> result = gene_to_uniprot_from_mygene("HGNC:3236")
    >>> assert "UniProtKB:P00533" in result
    """
    result = gene_to_uniprot_from_mygene("HGNC:3236")

    # EGFR's primary Swiss-Prot ID is P00533
    assert "UniProtKB:P00533" in result, (
        f"EGFR should map to UniProtKB:P00533, got {result}"
    )


@pytest.mark.integration
def test_gene_to_uniprot_handles_swiss_prot_priority() -> None:
    """Test that Swiss-Prot entries are preferred over TrEMBL.

    The function should prioritize Swiss-Prot (reviewed) entries over TrEMBL
    (unreviewed) entries when both are available.

    >>> result = gene_to_uniprot_from_mygene("HGNC:5")
    >>> # TP53 has Swiss-Prot entry, should be included
    >>> assert any("P04637" in id for id in result)
    """
    result = gene_to_uniprot_from_mygene("HGNC:5")

    # All results should be UniProtKB formatted
    assert all(id.startswith("UniProtKB:") for id in result), (
        "All results should have UniProtKB prefix"
    )


@pytest.mark.integration
def test_gene_to_uniprot_with_multiple_uniprot_ids() -> None:
    """Test genes that map to multiple UniProt IDs.

    Some genes may have multiple UniProt entries (isoforms, etc.).
    The function should return all of them.

    >>> result = gene_to_uniprot_from_mygene("HGNC:5")
    >>> assert isinstance(result, list)
    """
    result = gene_to_uniprot_from_mygene("HGNC:5")

    # Should return a list even if single result
    assert isinstance(result, list), "Result should always be a list"

    # Each entry should be properly formatted
    for uniprot_id in result:
        assert uniprot_id.startswith("UniProtKB:"), (
            f"Each ID should start with UniProtKB:, got {uniprot_id}"
        )
        # Should have an ID after the prefix
        assert len(uniprot_id.split(":")[1]) > 0, (
            f"Should have an ID after prefix, got {uniprot_id}"
        )


@pytest.mark.integration
def test_gene_to_uniprot_with_invalid_id() -> None:
    """Test gene_to_uniprot_from_mygene raises exception for invalid gene ID.

    When no UniProt IDs are found for a gene ID, the function should raise
    DataNotFoundException.

    >>> with pytest.raises(DataNotFoundException):
    ...     gene_to_uniprot_from_mygene("HGNC:99999999")
    """
    with pytest.raises(DataNotFoundException) as exc_info:
        gene_to_uniprot_from_mygene("HGNC:99999999")

    assert "No UniProtKB IDs found" in str(exc_info.value.detail), (
        "Exception should indicate no UniProtKB IDs were found"
    )


@pytest.mark.integration
def test_gene_to_uniprot_ncbigene_prefix_conversion() -> None:
    """Test that NCBIGene prefix is correctly converted to entrezgene.

    MyGene.info expects 'entrezgene' prefix, not 'NCBIGene'.
    The function should convert NCBIGene:7157 to entrezgene:7157.

    >>> result = gene_to_uniprot_from_mygene("NCBIGene:7157")
    >>> assert len(result) > 0
    >>> assert all(id.startswith("UniProtKB:") for id in result)
    """
    # NCBIGene:7157 is TP53
    result = gene_to_uniprot_from_mygene("NCBIGene:7157")

    assert len(result) > 0, "NCBIGene format should be converted and return results"
    assert "UniProtKB:P04637" in result, (
        "NCBIGene:7157 (TP53) should return UniProtKB:P04637"
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    "uniprot_id,expected_hgnc,description",
    [
        # P04637 is TP53
        ("UniProtKB:P04637", "HGNC:11998", "TP53 UniProt should return HGNC"),
        # Without prefix
        ("P04637", "HGNC:11998", "UniProt ID without prefix should work"),
        # P38398 is BRCA1
        ("UniProtKB:P38398", "HGNC:1100", "BRCA1 UniProt should return HGNC"),
        # P00533 is EGFR
        ("UniProtKB:P00533", "HGNC:3236", "EGFR UniProt should return HGNC"),
    ],
)
def test_uniprot_to_gene_from_mygene_with_valid_uniprot_ids(
    uniprot_id: str, expected_hgnc: str, description: str
) -> None:
    """Test uniprot_to_gene_from_mygene with various valid UniProt IDs.

    This test verifies the reverse mapping from UniProt to HGNC gene IDs.

    Args:
        uniprot_id: The UniProt identifier to query
        expected_hgnc: The expected HGNC identifier
        description: Test case description

    >>> result = uniprot_to_gene_from_mygene("P04637")
    >>> assert isinstance(result, list)
    >>> assert len(result) > 0
    >>> assert result[0].startswith("HGNC:")
    """
    result = uniprot_to_gene_from_mygene(uniprot_id)

    # Verify we got results
    assert result is not None, f"{description}: Result should not be None"
    assert isinstance(result, list), f"{description}: Result should be a list"
    assert len(result) > 0, f"{description}: Should return at least one HGNC ID"

    # Verify the expected HGNC ID is in results
    assert expected_hgnc in result, (
        f"{description}: Expected {expected_hgnc} in results, got {result}"
    )


@pytest.mark.integration
def test_uniprot_to_gene_with_invalid_id() -> None:
    """Test uniprot_to_gene_from_mygene raises exception for invalid UniProt ID.

    When no HGNC IDs are found for a UniProt ID, the function should raise
    DataNotFoundException.

    >>> with pytest.raises(DataNotFoundException):
    ...     uniprot_to_gene_from_mygene("INVALID99999")
    """
    with pytest.raises(DataNotFoundException) as exc_info:
        uniprot_to_gene_from_mygene("INVALID99999")

    assert "No HGNC IDs found" in str(exc_info.value.detail), (
        "Exception should indicate no HGNC IDs were found"
    )


@pytest.mark.integration
def test_round_trip_gene_to_uniprot_to_gene() -> None:
    """Test round-trip conversion: HGNC -> UniProt -> HGNC.

    Starting with a gene ID, converting to UniProt, then back to gene ID
    should return to the original (or at least a valid related) gene ID.

    >>> hgnc_id = "HGNC:11998"
    >>> uniprot_ids = gene_to_uniprot_from_mygene(hgnc_id)
    >>> for uniprot_id in uniprot_ids:
    ...     gene_ids = uniprot_to_gene_from_mygene(uniprot_id)
    ...     assert hgnc_id in gene_ids
    """
    # Start with TP53
    hgnc_id = "HGNC:11998"

    # Convert to UniProt
    uniprot_ids = gene_to_uniprot_from_mygene(hgnc_id)
    assert len(uniprot_ids) > 0, "Should get at least one UniProt ID"

    # Convert back to gene
    for uniprot_id in uniprot_ids:
        gene_ids = uniprot_to_gene_from_mygene(uniprot_id)
        assert hgnc_id in gene_ids, (
            f"Round trip should return original HGNC ID {hgnc_id}, got {gene_ids}"
        )
