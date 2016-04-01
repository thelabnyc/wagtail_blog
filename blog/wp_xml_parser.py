from html.parser import HTMLParser
from io import BytesIO
import datetime
import re
import time

import lxml.etree as etree
import lxml.html as HM

htmlparser = HTMLParser()


class XML_parser(object):

    def __init__(self, xml_path):
        # TODO: yup, that's the whole file in memory
        xml_string = self.prep_xml(open(xml_path, 'r').read())
        root = etree.XML(xml_string)
        self.chan = root.find("channel")
        self.category_dict = self.get_category_dict(self.chan)
        self.tags_dict = self.get_tags_dict(self.chan)

    @staticmethod
    def get_category_dict(chan):
        cats = [e for e in chan.getchildren() if '{wp}category' in e.tag]
        cats_dict = {}
        for cat in cats:
            slug = cat.find('.//{wp}category_nicename').text
            cats_dict[slug] = {'slug':slug,
                               'name': htmlparser.unescape(cat.find("./{wp}cat_name").text),
                               'parent':cat.find("./{wp}category_parent").text,
                               'taxonomy': 'category'}

        # replace parent strings with parent dicts:
        for slug, item in cats_dict.items():
            parent_name = item.get('parent')
            if parent_name:
                cats_dict[slug]['parent'] = cats_dict[parent_name]

        return cats_dict

    def get_tags_dict(self, chan):
        tags = [e for e in chan.getchildren() if e.tag[-3:] == "tag"]
        tags_dict = {}
        # these matches assume we've cleaned up xlmns
        for e in tags:
            slug = e.find('.//{wp}tag_slug').text
            tags_dict[slug] = {'slug':slug}
            name = htmlparser.unescape(e.find('.//{wp}tag_name').text) # need some regex parsing here
            tags_dict[slug]['name'] = name
            tags_dict[slug]['taxonomy'] = 'post_tag'
        return tags_dict

    @staticmethod
    def remove_encoding(xml_string):
        """
        removes encoding statement and
        changes xmlns to tag:item to tag:tag
        >>> xp = XML_parser
        >>> test_xmlns = r'<?xml encoding="some encoding" ?> test'
        >>> xp.remove_encoding(test_xmlns)
        ' test'
        """
        xml_string = re.sub(r'^<.*encoding="[^\"]*\"[^>]*>', '', xml_string)
        return xml_string

    @staticmethod
    def remove_xmlns(xml_string):
        """
        changes the xmlns (XML namespace) so that values are
        replaced with the string representation of their key
        this makes the import process for portable

        >>> xp = XML_parser
        >>> test_xmlns = r'<rss version="2.0" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/">'
        >>> xp.remove_xmlns(test_xmlns)
        '<rss version="2.0" xmlns:excerpt="excerpt">'
        """
        # splitting xml into sections, pre_chan is preamble before <channel>
        pre_chan, chan, post_chan= xml_string.partition('<channel>')
        # replace xmlns statements on preamble
        pre_chan = re.sub(r'xmlns:(?P<label>\w*)\=\"(?P<val>[^\"]*)\"',
                             r'xmlns:\g<label>="\g<label>"',
                             pre_chan)
        # piece back together
        return pre_chan + chan + post_chan

    def prep_xml(self, xml):
        return self.remove_xmlns(self.remove_encoding(xml))


    def item_dict(self, item):
        """
        create a default dict of values, including
        category and tag lookup
        """
        # mocking wierd JSON structure
        ret_dict = {"terms":{"category":[],"post_tag":[]}}
        for e in item:
            # is it a category or tag??
            if "category" in e.tag:
                # get details
                slug = e.attrib["nicename"]
                name = htmlparser.unescape(e.text)
                # lookup the category or create one
                cat_dict = self.category_dict.get(slug) or {"slug":slug,
                                                             "name":name,
                                                             "taxonomy":"category"}
                ret_dict['terms']['category'].append(cat_dict)

            elif e.tag[-3:] == 'tag':
                # get details
                slug = e.attrib.get("tag_slug")
                name = htmlparser.unescape(e.text)
                # lookup the tag or create one
                tag_dict = self.tags_dict.get(slug) or {"slug":slug,
                                                        "name":name,
                                                        "taxonomy":"post_tag"}

                ret_dict['terms']['post_tag'].append(tag_dict)
            # else use tagname:tag inner test
            else:
                ret_dict[e.tag] = e.text
            # remove empty accumulators
        empty_keys = [k for k,v in ret_dict["terms"].items() if not v]
        for k in empty_keys:
            ret_dict["terms"].pop(k)
        return ret_dict

    @staticmethod
    def convert_date(d, custom_date_string=None):
        """
        for whatever reason, sometimes WP XML has unintelligible
        datetime strings for pubDate.
        In this case default to custom_date_string or today
        >>> xp = XML_parser
        >>> xp.convert_date("Mon, 30 Mar 2015 11:11:11 +0000")
        '2015-03-30'
        """
        try:
            date =  time.strftime("%Y-%m-%d", time.strptime(d, '%a, %d %b %Y %H:%M:%S %z'))
        except ValueError:
            date = custom_date_string or datetime.datetime.today().strftime("%Y-%m-%d")
        return date

    def translate_item(self, item_dict):
        """cleanup item keys to match API json format"""
        if not item_dict.get('title'):
            return None
        ret_dict = {}
        # slugify post title if no slug exists
        ret_dict['slug']= item_dict.get('{wp}post_name') or re.sub(item_dict['title'],' ','-')
        ret_dict['ID']= item_dict['guid']
        ret_dict['title']= item_dict['title']
        ret_dict['description']= item_dict['description']
        ret_dict['content']= item_dict['{content}encoded']
        # fake user object
        ret_dict['author']= {'username':item_dict['{dc}creator'],
                             'first_name':'',
                             'last_name':''}
        ret_dict['terms']= item_dict.get('terms')
        ret_dict['date']= self.convert_date(item_dict['pubDate'])
        # ret_dict['featured_image'] = None
        return ret_dict


    def get_posts_data(self):
        """
        given a WordPress xml export file, will return list
        of dictionaries with keys that match
        the expected json keys of a wordpress API call
        >>> xp = XML_parser('example_export.xml')
        >>> json_vals = {"slug","ID", "title","description", "content", "author", "terms", "date", }
        >>> data = xp.get_posts_data()
        >>> assert [ val in json_vals for val in data[0].keys() ]
        """
        items = self.chan.findall("item") #(e for e in chan.getchildren() if e.tag=='item')
        # turn item element into a generic dict
        item_dict_gen = (self.item_dict(item) for item in items)
        # transform the generic dict to one with the expected JSON keys
        all_the_data = [self.translate_item(item) for item in item_dict_gen if self.translate_item(item)]
        return all_the_data


if __name__ == "__main__":
    import doctest
    doctest.testmod()
