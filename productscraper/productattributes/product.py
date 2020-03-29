class Product(object):
    def __init__(self, site, sku, url , instock, variations):
        site = site
        sku = sku
        url = url
        instock = instock
        variations = variations

    def __str__(self):
        return self.sku
