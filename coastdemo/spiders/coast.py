# -*- coding: utf-8 -*-
import scrapy
from ..items import CoastdemoItem
from requests import get
from random import choice
from pyquery import PyQuery as pq
from collections import OrderedDict

BASE_URL = 'https://www.coast-stores.com'


def random_headers():
    """Returns random request headers"""
    fake_headers = [
        u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36',
        u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1944.0 Safari/537.36',
        u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36',
        u'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-us) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
        u'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36',
        u'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2224.3 Safari/537.36',
        u'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36',
        u'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2049.0 Safari/537.36',
        u'Mozilla/5.0 (X11; OpenBSD amd64; rv:28.0) Gecko/20100101 Firefox/28.0',
        u'Opera/9.80 (X11; Linux i686; U; hu) Presto/2.9.168 Version/11.50'
    ]
    return {'user-agent': choice(fake_headers)}


def type_select(breadcrumbs):
    """Select which type of ad is based on website breadcrumbs"""
    category_types = OrderedDict()
    category_types['shoes'] = 'A'
    category_types['bag'] = 'B'
    category_types['jewelry'] = 'J'
    category_types['accessories'] = 'R'

    # Base type
    item_type = 'A'

    for entry in breadcrumbs:
        if not len(entry) or entry.text is None:
            continue

        for key in category_types.keys():
            if key in entry.text.lower():
                return category_types[key]

    return item_type


def extract(items_list, index=0, default=''):
    if not len(items_list):
        return default
    else:
        try:
            result = items_list[index]
            return result
        except IndexError:
            return default


class CoastSpider(scrapy.Spider):
    name = 'coast'
    allowed_domains = ['www.coast-stores.com', 'www.coast.btxmedia.com']
    start_urls = ['https://www.coast-stores.com']

    def parse(self, response):
        # Creates a XML tree from sitemap
        tree = pq(response.text)
        categories = tree.find('li[class$="nav-level-1-list"] > a')

        # Extra request for extra ads hidden in the xml sitemap
        xml_tree = pq(get('https://coast.btxmedia.com/pws/client/sitemap/PWS/ProductDetailPagesX_0.xml').content)
        urls = xml_tree.remove_namespaces().find('loc')
        xml_sitemap = [url.text for url in urls if url.text is not None and url.text.startswith('http')]

        # Iterates on each child
        for category in categories:
            # Sanity check
            if 'href' not in category.attrib or '/page/' in category.attrib['href']:
                continue

            url = ''.join([response.url, category.attrib['href']])

            yield scrapy.Request(
                url=url,
                headers=random_headers(),
                callback=self.parse_pages,
                meta={'xml_sitemap': xml_sitemap}
            )

    def parse_pages(self, response):
        tree = pq(response.text)

        items_count = tree.find('h4').eq(0).text()
        try:
            count_str = ''.join(number for number in items_count if number.isdigit())

            if not count_str:
                return

            count = int(count_str)

        except ValueError:
            return

        if count % 60:
            pages = (count/60) + 1
        else:
            pages = count/60

        for page in xrange(1, pages+1):
            url = ''.join([response.url, '?page=', str(page)])

            yield scrapy.Request(
                url=url,
                headers=random_headers(),
                callback=self.parse_item_list,
                meta={'xml_sitemap': response.meta['xml_sitemap']}
            )

    def parse_item_list(self, response):
        tree = pq(response.text)
        items = tree.find('a[class="product-block__image"]')

        xml_sitemap = response.meta['xml_sitemap']

        for item in items:
            if 'href' not in item.attrib:
                continue

            url = ''.join([BASE_URL, item.attrib['href']])

            # Removing duplicates from xml
            if url in xml_sitemap:
                xml_sitemap.remove(url)

            yield scrapy.Request(
                url=url,
                headers=random_headers(),
                callback=self.parse_item
            )

        # Crawling ads only found in xml
        for url in xml_sitemap:
            yield scrapy.Request(
                url=url,
                headers=random_headers(),
                callback=self.parse_item
            )

    def parse_item(self, response):
        tree = pq(response.text)
        item = CoastdemoItem()

        # Code
        item['code'] = response.url.split('/')[-1]

        # Name
        name = tree('meta[itemprop="name"]')
        item['name'] = name[0].attrib['content'].title() if len(name) else ''

        # Description
        description = tree('meta[itemprop="description"]')
        item['description'] = description[0].attrib['content'] if len(description) else ''

        # Designer
        designer = tree('meta[name="author"]')
        item['designer'] = designer[0].attrib['content'] if len(designer) else ''

        # Raw_color
        raw_color = tree('img[alt="colour swatch"]')
        try:
            raw_color = raw_color[0].getnext().text if len(raw_color) else None
            if not raw_color:
                raw_color = None
        except AttributeError:
            raw_color = None
        item['raw_color'] = raw_color

        # Price
        price = tree('p[class="prod-content__price"] > del').eq(0).text()
        if len(price):
            price = price.replace(u'\xa3', '')
        else:
            price = tree('p[class="prod-content__price"] > strong').eq(0).text()
            price = price.replace(u'\xa3', '') if len(price) else '0'
        item['price'] = price + '.00' if price else '0.00'

        # Currency
        item['currency'] = 'GBP'

        # Sale_discount
        try:
            discount = tree('strong[class="now-price"]').eq(0).text().replace(u'\xa3', '')
            item['sale_discount'] = round((float(price) - float(discount))/float(price)*100, 1)
        except:
            item['sale_discount'] = 0.0

        # Link
        link = tree('link[rel="canonical"]')
        item['link'] = link[0].attrib['href'] if len(link) else response.url

        # Type
        item['type'] = type_select(tree('span[class="breadcrumbs__desc text-link"]'))

        # Gender
        item['gender'] = 'F'  # Hardcoded since website has only female items

        # Stock_status
        stock = tree('a[class="highlight "]')
        stock_status = {}
        for stock_item in stock:
            text = stock_item.text
            href = False
            if 'href' in stock_item.attrib:
                href = True
            stock_status[text] = href

        if not stock_status:
            is_one_size = tree('a[class="highlight single-size"]')
            if len(is_one_size):
                stock_status['One size'] = True
            else:
                stock_status['N/A'] = True
        item['stock_status'] = stock_status

        # Skus
        skus = tree('meta[name="keywords"]')
        item['skus'] = skus[0].attrib['content'].split(',') if len(skus) else []

        # Image_urls
        item['image_urls'] = [img.attrib['src'] for img in tree('img[data-product="{}"]'.format(item['code']))]

        yield item
