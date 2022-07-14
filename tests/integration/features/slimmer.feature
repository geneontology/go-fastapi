Feature: slimmer routes work as expected
## Map2slim for GO with MGI

 Scenario: slimmer routes work as expected
    Given the "/bioentityset/slimmer/function endpoint" is queried with gene "MGI:98371" and slim "GO:0003824,GO:0004872,GO:0005102,GO:0005215,GO:0005198,GO:0008092,GO:0003677,GO:0003723,GO:0001071,GO:0036094,GO:0046872,GO:0030246,GO:0008283,GO:0071840,GO:0051179,GO:0032502,GO:0000003,GO:0002376,GO:0050877,GO:0050896,GO:0023052,GO:0010467,GO:0019538,GO:0006259,GO:0044281,GO:0050789,GO:0005576,GO:0005829,GO:0005856,GO:0005739,GO:0005634,GO:0005694,GO:0016020,GO:0071944,GO:0030054,GO:0042995,GO:0032991"
    Then the response status code is "200"
    And the response should have an association with subject.label of  "Sox9"
    And the response contains an association with subject.id of "MGI:98371"
    And the response should have "GO:0010467" in the slim
