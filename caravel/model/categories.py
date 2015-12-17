from google.appengine.ext import ndb

class CategoriesMixin(ndb.Model):
    CATEGORIES_LIST = [
        ("apartments", "Apartments"),
        ("subleases", "Subleases"),
        ("appliances", "Appliances"),
        ("bikes", "Bikes"),
        ("books", "Books"),
        ("cars", "Cars"),
        ("electronics", "Electronics"),
        ("employment", "Employment"),
        ("furniture", "Furniture"),
        ("miscellaneous", "Miscellaneous"),
        ("services", "Services"),
        ("wanted", "Wanted"),
    ]
    CATEGORIES_DICT = dict(CATEGORIES_LIST)

    categories = ndb.StringProperty(repeated=True)
