Feature: bioentity function (GO) routes work as expected

  Scenario: test function endpoint
    Given the bioentity/gene/id/function endpoint is queried with "ZFIN:ZDB-GENE-050417-357"
    Then the response status code is "200"
    And the response contains an association with object.id of "GO:0030500"
    And the response should have an association with object.label of "regulation of bone mineralization"

  Scenario: User fetches all GO functional assignments for a human gene using a NCBI ID, note GO may annotate to UniProt
     Given the /bioentity/gene/id/function endpoint
     When the content is converted to JSON
     Then the JSON should have some JSONPath "associations[*].object.id" with "string" "GO:0001755"
     And the JSON should have some JSONPath "associations[*].object.label" with "string" "neural crest cell migration"

  Scenario: User fetches all GO functional assignments for a human gene using a HGNC ID, note GO may annotate to UniProt
     Given a path "/bioentity/gene/HGNC:6081/function?rows=100"
     When the content is converted to JSON
     Then the JSON should have some JSONPath "associations[*].object.id" with "string" "GO:0005158"
     And the JSON should have some JSONPath "associations[*].object.label" with "string" "insulin receptor binding"