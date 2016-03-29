from io import BytesIO
import datetime
import re
import time

import lxml.etree as etree
import lxml.html as HM


def remove_encoding(xml_string):
    """
    removes encoding statement and
    changes xmlns to tag:item to tag:tag

    >>> test_xmlns = r'<?xml encoding="some encoding" ?> test' 
    >>> remove_encoding(test_xmlns)
    ' test'
    """
    # pre_chan, chan, post_chan= xml_string.partition('<channel>')
    # remove encoding
    xml_string = re.sub(r'^<.*encoding="[^\"]*\"[^>]*>', '', xml_string)
    return xml_string

def remove_xmlns(xml_string):
    """
    >>> test_xmlns = r'<rss version="2.0" xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/">'
    >>> remove_xmlns(test_xmlns)
    '<rss version="2.0" xmlns:excerpt="excerpt">'
    """
    pre_chan, chan, post_chan= xml_string.partition('<channel>')
    pre_chan = re.sub(r'xmlns:(?P<label>\w*)\=\"(?P<val>[^\"]*)\"',
                         r'xmlns:\g<label>="\g<label>"',
                         pre_chan)
    return pre_chan + chan + post_chan

prep_xml = lambda x : remove_xmlns(remove_encoding(x))

def item_dict(item):
    #{e.tag:e.text for e in item}
    ret_dict = {"terms":{}}
    for e in item:
        if e.tag == "category":
            ret_dict["terms"].update({k:v for k,v in e.attrib.items()})
        else:
            ret_dict[e.tag] = e.text
    return ret_dict

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

def translate_item(item_dict):
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
    ret_dict['date']= convert_date(item_dict['pubDate'])
    # ret_dict['featured_image'] = None
    return ret_dict

def xml_import(xml_location):
    """given a WordPress xml export file, will return list 
    of dictionaries with keys that match
    the expected json keys of a wordpress API call

    >>> json_vals = {"slug","ID", "title","description", "content", "author", "terms", "date", }
    >>> data = xml_import('greenkeyintranet.xml')
    >>> assert [ val in json_vals for val in data[0].keys() ]
    """
    # TODO: don't load the whole damn thing into memory
    xml_string = open(xml_location, 'r').read()
    xml_string = prep_xml(xml_string)
    root = etree.XML(xml_string)
    # The chanel section should be the first element, where rss is root
    chan = root.find("channel")
    items = chan.findall("item") #(e for e in chan.getchildren() if e.tag=='item')
    # turn item element into a generic dict
    item_dict_gen = (item_dict(item) for item in items)
    # transform the generic dict to one with the expected JSON keys
    all_the_data = [translate_item(item) for item in item_dict_gen if translate_item(item)]
    return all_the_data


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    # print(xml_export_to_list_of_dicts('greenkeyintranet.xml')[:10])
