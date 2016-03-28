import lxml.etree as etree
import lxml.html as HM
import re
from io import BytesIO

def replace_xmlns(xml_string):
    """
    chagnes xmlns to tag:item to tag:tag
    >>> test_xmlns = 'xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"'
    >>> replace_xmlns(test_xmlns)
    'xmlns:excerpt="excerpt"'
    """
    pre_chan, chan, post_chan= xml_string.partition('<channel>')
    # make this quick, only replace xmlns in prechannel, where it should be
    pre_chan = re.sub(r'xmlns:(?P<label>\w*)\=\"(?P<val>.*)\"',
                         r'xmlns:\g<label>="\g<label>"',
                         pre_chan)
    return pre_chan + chan + post_chan






# ## does every item have the same amount of keys?
# # keys_list = [set(i.keys()) for i in item_dict_gen()]
# # all_keys = keys_list[0].union(*keys_list[1:])
# # shared_keys = keys_list[0].intersection(*keys_list[1:])
# # optional_keys = all_keys - shared_keys
# # items_with_opt_keys = sorted([(d.get('link'),list(d.keys()-shared_keys)) for d in item_dict_gen() if optional_keys.intersection(d.keys())])
#
#
# # # Can I find all the expected json vals from json import
# # json_vals = ["slug", # {wp}post_naem
# #             "ID", # guid?
# #             "title", #
# #             "description", #
# #             "content", #
# #             "author", # creator?
# #             "terms", ## WTF??
# #             "date", # post date?
# #             "featured_image",]
# #
# # shared_keys
# # items_with_img = [item for item in item_dict_gen() if "<img" in item["{content}encoded"]]
#
# # ## Don't need this probably
# # def grab_img_urls_from_string(content):
# #     # try XML?
# #     if not "<img" in content:
# #         return None
# #     try:
# #         tree = HM.fromstring(content)
# #     except XMLSyntax:
# #         print("couldn't parse")
# #     if tree is not None:
# #         img_tags = tree.findall(".//img")
# #         if img_tags is not None:
# #             return [e.attrib['src'] for e in img_tags] 
# #
# # assert grab_img_url_item(items_with_img[0]['{content}encoded'])
# # img_links = [grab_img_urls_from_string(item['{content}encoded']) for item in item_dict_gen() if grab_img_urls_from_string(item['{content}encoded'])]
# #
#
#

def translate_item(item_dict):
    """cleanup item keys to match API json format"""
    ret_dict = {}
    # assume we have the values we need, fail hard otherwise
    ret_dict['slug']= item_dict['{wp}post_name']
    ret_dict['ID']= item_dict['guid']
    ret_dict['title']= item_dict['title']
    ret_dict['description']= item_dict['description']
    ret_dict['content']= item_dict['{content}encoded']
    ret_dict['author']= item_dict['{dc}creator']
    # ret_dict['terms']= ""
    ret_dict['date']= item_dict['pubDate']
    # ret_dict['featured_image'] = None
    return ret_dict

def xml_export_to_list_of_dicts(xml_location):
    """given a WordPress xml export file, will return list 
    of dictionaries with keys that match
    the expected json keys of a wordpress API call
    """
    # TODO: don't load the whole damn thing into memory
    xml_string = open(xml_location, 'r').read()
    xml_string = replace_xmlns(xml_string)
    root = etree.XML(xml_string)
    # The chanel section should be the first element, where rss is root
    chan = root.find("channel")
    items = (e for e in chan.getchildren() if e.tag=='item')
    # turn item element into a generic dict
    item_dict = lambda item: {e.tag:e.text for e in item}
    item_dict_gen = (item_dict(item) for item in items)
    # transform the generic dict to one with the expected JSON keys
    all_the_data = [translate_item(item) for item in item_dict_gen]
    return all_the_data


if __name__ == "__main__":
    import doctest
    doctest.testmod()
    print(xml_export_to_list_of_dicts('greenkeyintranet.xml'))
