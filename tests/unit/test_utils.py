"""Unit tests for the endpoints in the utils module."""
import logging
import unittest

from curies import Converter
from fastapi.testclient import TestClient

from app.main import app
from app.utils.prefix_utils import get_converter

test_client = TestClient(app)
logging.basicConfig(filename="combined_access_error.log", level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger()

gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]


class TestPrefixUtils(unittest.TestCase):

    """test the basic utils methods."""

    def test_prefix_utils(self):
        """
        Test the prefix utilities.

        :return: None
        """
        converter = get_converter("go")
        cmaps = converter.prefix_map
        self.assertEqual(cmaps["MGI"], "http://identifiers.org/mgi/MGI:")


if __name__ == "__main__":
    unittest.main()
