Feature: bioentity function (GO) routes work as expected

  Scenario: test function endpoint
    Given the API is queried with "ZFIN:ZDB-GENE-050417-357"
    Then the response status code is "200"
    And the response contains results for a "GO:0030500"
