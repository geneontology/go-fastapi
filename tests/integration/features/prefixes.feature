Feature: Expansion and contraction of URIs

 Scenario: Client code requires list of all prefixes in use
    Given the "/api/identifier/prefixes" is queried
    Then the response status code is "200"
    Then the content should contain "UBERON"

### GO connections

 Scenario: Contract a GO URI to a GO OBO-style ID
    Given the "/api/identifier/prefixes/contract/" endpoint is queried with "http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGO_0008150"
    Then the response status code is "200"
    Then the content should contain "GO:0008150"

 Scenario: Expand a GO ID to a URI
    Given the "/api/identifier/prefixes/expand/" endpoint is queried with "GO:0008150"
    Then the response status code is "200"
    Then the content should contain "http://purl.obolibrary.org/obo/GO_0008150"