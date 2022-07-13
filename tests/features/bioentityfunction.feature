Feature: bioentity function (GO) routes work as expected
# anything here is just treated as comments
#
# given sets an initial state
# when takes an action
# then verifies the outcome

    Scenario: User fetches all GO functional annotations for a zebrafish gene
        Given the go-fastapi test-client is queried with a value
        Then the endpoint should return successfully