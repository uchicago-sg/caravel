import collections
from caravel.storage.cache import cache, batchcache, DBEncoder, DBDecoder
from google.appengine.ext import db


def test_cache_behavior():
    invocations = collections.Counter()

    @cache
    def single_function(kind):
        invocations[kind] += 1
        return kind + "!"

    @batchcache
    def batch_function(args):
        result = []
        for (vargs, kwargs) in args:
            assert len(kwargs) + len(vargs) == 1
            arg = vargs[0] if vargs else kwargs["kind"]
            invocations[arg] += 1
            result.append(arg + "!")
        return result

    for function in [single_function, batch_function]:
        assert function("a") == "a!"
        assert function("a") == "a!"
        assert function(kind="c") == "c!"

        function.invalidate("a")
        assert function("a") == "a!"

        assert tuple(function.batch([("a", {}), ("d", {})])) == ("a!", "d!")

    assert invocations["a"] == 6
    assert invocations["c"] == 2
    assert invocations["d"] == 2
    assert len(invocations) == 3


class Entity(db.Model):
    a = db.StringProperty()


def test_encode_entity():
    ent = Entity(a="foo bar", key_name="key")
    ent.put()
    ent2 = DBDecoder().decode(DBEncoder().encode(ent))
    assert ent2.key().name() == "key"
    assert ent2.a == "foo bar"

    assert DBDecoder().decode(DBEncoder().encode({"x": 1}))["x"] == 1
