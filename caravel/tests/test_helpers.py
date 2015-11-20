from caravel.storage import entities, helpers


def test_lookups():
    a = entities.Listing(title="lista", body="ba", key_name="foo")
    a.put()
    assert helpers.lookup_listing("foo").title == "lista"

    a.title = "listb"
    a.put()
    assert helpers.lookup_listing("foo").title == "lista"

    helpers.invalidate_listing(a)
    assert helpers.lookup_listing("foo").title == "listb"


def test_search():
    entities.Listing(title="title for test",
                     posting_time=1.0e5, key_name="search_test").put()

    assert tuple(helpers.fetch_shard("title")) == ("search_test",)
    assert (tuple(x.permalink for x in helpers.run_query("title for test")) ==
            ("search_test",))

    ent = entities.Listing(title="new title",
                           posting_time=1.0e5, key_name="search_test")
    ent.put()
    helpers.invalidate_listing(ent)

    assert not helpers.run_query("title for test")


def test_inquiries():
    ent = entities.Listing(title="car", key_name="entfortest")
    ent.put()

    helpers.add_inqury(ent, "e@mail", "foobar")
    helpers.add_inqury(ent, "e@mail", "foobar")
    helpers.add_inqury(ent, "e2@mail", "foobar")

    ent = helpers.lookup_listing("entfortest")
    assert set(ent.buyers) == set(["e@mail", "e2@mail"])
    assert len(ent.buyers) == 2
