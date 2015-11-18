from caravel.storage import entities

def test_query_folding():
    expectations = {
        "is:Foos": "is:Foos",
        "CaTs": "cat",
        "e@mails": "e@mails",
        "[foo": "foo",
    }
    
    for key, value in expectations.items():
        assert entities.fold_query_term(key) == value

def test_properties():
    ent = entities.Listing(
        title="Ma Listing",
        body="Body, Text!",
        seller="e@mail",
        key_name="xyz",
        posting_time=10.0,
    )
    
    assert ent.permalink == "xyz"
    assert ent.primary_category == "miscellaneous"
    ent.categories = ["books", "cars"]
    assert ent.primary_category == "books"
    print set(ent.keywords)
    assert set(ent.keywords) == set(["ma", "listing", "body", "text", "e@mail",
                                     "book", "car", "price:free"])
