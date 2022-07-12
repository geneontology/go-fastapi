from fastapi.testclient import TestClient
from app.main import app
import pytest
from pprint import pprint

test_client = TestClient(app)


gene_ids = ["ZFIN:ZDB-GENE-980526-388", "ZFIN:ZDB-GENE-990415-8"]
go_ids = ["GO:0008150"]
subsets = ["goslim_agr"]
shared_ancestors = [("GO:0006259", "GO:0046483")]

