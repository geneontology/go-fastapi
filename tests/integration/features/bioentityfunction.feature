Feature: bioentity function (GO) routes work as expected

  Scenario: test function endpoint
    Given the "bioentity/gene/id/function endpoint" is queried with "ZFIN:ZDB-GENE-050417-357"
    Then the response status code is "200"
    And the response contains an association with object.id of "GO:0030500"
    And the response should have an association with object.label of "regulation of bone mineralization"

  Scenario: User fetches all GO functional assignments for a human gene using an HGNC id
     Given the "/bioentity/gene/id/function endpoint" is queried with "HGNC:6081"
     Then the response status code is "200"
     And the response contains an association with object.id of "GO:0005158"
     And the response should have an association with object.label of "insulin receptor binding"

  Scenario: User fetches all GO functional assignments for a human gene using a NCBI ID
     Given a path "/bioentity/gene/id/function endpoint" is queried with "NCBIGene:6469"
     Then the response status code is "200"
     And the response contains an association with object.id of "GO:0001755"
     And the response should have an association with object.label of "neural crest cell migration"
