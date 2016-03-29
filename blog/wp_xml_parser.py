from io import BytesIO
import datetime
import re
import time

import lxml.etree as etree
import lxml.html as HM

class XML_parser(object):

    def __init__(self, xml_path):
        # TODO: yup, that's the whole file in memory
        if not xml_path:
            return None
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
            cats_dict['slug'] = {'slug':cat.find("./{wp}category_nicename").text, 
                                 'name':cat.find("./{wp}cat_name").text}
            cats_dict['taxonomy'] = 'category'
        return cats_dict

    @staticmethod
    def get_tags_dict(chan):
        terms = [e for e in chan.getchildren() if 'term' in e.tag]
        terms_dict = {}
        for e in terms:
            slug = e.find('.//{wp}term_slug').text
            terms_dict[slug] = {'slug':slug}
            name = e.find('.//{wp}term_name').text # need some regex parsing here
            terms_dict[slug]['name'] = name
            terms_dict[slug]['taxonomy'] = 'post-tag'
        return terms_dict

    @staticmethod
    def remove_encoding(xml_string):
        """
        removes encoding statement and
        changes xmlns to tag:item to tag:tag
        >>> xp = XML_parser('')
        >>> test_xmlns = r'<?xml encoding="some encoding" ?> test' 
        >>> xp.remove_encoding(test_xmlns)
        ' test'
        """
        # pre_chan, chan, post_chan= xml_string.partition('<channel>')
        # remove encoding
        xml_string = re.sub(r'^<.*encoding="[^\"]*\"[^>]*>', '', xml_string)
        return xml_string

    @staticmethod
    def remove_xmlns(xml_string):
        """
        >>> xp = XML_parser('')
        >>> test_xmlns = r'<rss version="2.0" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/">'
        >>> xp.remove_xmlns(test_xmlns)
        '<rss version="2.0" xmlns:excerpt="excerpt">'
        """
        pre_chan, chan, post_chan= xml_string.partition('<channel>')
        pre_chan = re.sub(r'xmlns:(?P<label>\w*)\=\"(?P<val>[^\"]*)\"',
                             r'xmlns:\g<label>="\g<label>"',
                             pre_chan)
        return pre_chan + chan + post_chan

    def prep_xml(self, xml): 
        return self.remove_xmlns(self.remove_encoding(xml))


    def item_dict(self, item):
        """
        create a default dict of values, including
        category and tag lookup
        """
        # mocking wierd JSON structure
        ret_dict = {"terms":{}}
        for e in item:
            # is it a category or tag??
            if "category" in e.tag:
                slug = e.attrib.get("nicename")
                found_category_dict = None
                # is it a category?
                if e.attrib["domain"] == "category":
                    found_category_dict = self.category_dict.get(slug)
                # or is it a tag?
                elif e.attrib["domain"] == "media-category":
                    found_category_dict = self.tags_dict.get(slug)
                if found_category_dict:
                    ret_dict["terms"][slug] = [found_category_dict] 
                # or we have no idea?
                else:
                    # create a dummy dict as a post-tag
                    name = e.text #TODO: regex parsing here??
                    ret_dict["terms"][slug] = [{"slug":slug,
                                              "name":name,
                                              "taxonomy":"post-tag"}]
            # all other values get tag:text
            else:
                ret_dict[e.tag] = e.text
        return ret_dict

    @staticmethod
    def convert_date(d, custom_date_string=None):
        """
        for whatever reason, sometimes WP XML has unintelligible 
        datetime strings for pubDate.
        In this case default to custom_date_string or today
        """
        try:
            date =  time.strftime("%Y-%m-%d", time.strptime(d[:16], '%a, %d %b %Y'))
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
        """given a WordPress xml export file, will return list 
        of dictionaries with keys that match
        the expected json keys of a wordpress API call
        >>> xp = XML_parser('greenkeyintranet.xml')
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
    # print(xml_export_to_list_of_dicts('greenkeyintranet.xml')[:10])
