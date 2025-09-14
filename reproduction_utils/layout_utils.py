import hashlib
import re
from bs4 import BeautifulSoup, Tag
from lxml import etree
from lxml.etree import _Element
from os.path import dirname, abspath
import sys
sys.path.append(dirname(abspath(__file__)))
from llm_helper import language_query

class ViewNotFoundException(Exception):
    pass


class Layout:
    def __init__(self, layout_path, index=None):
        self.etree_layout = etree.parse(layout_path)
        self.id = index

    # get the view with a specified bound
    def get_tgt_view_by_bound(self, bound, force_to_be_clickable=True) -> BeautifulSoup:
        clickables = self.etree_layout.xpath(f"//node[@bounds='{bound}']")
        if force_to_be_clickable:
            clickables = self.etree_layout.xpath(f"//node[@bounds='{bound}' and @clickable='true']")
            
        if len(clickables) == 0:
            raise ViewNotFoundException()
        if len(clickables) > 0:
            tgt_view = clickables[0]
            tgt_view.attrib['x_path'] = self.etree_layout.getpath(clickables[0])
            return tgt_view
        

    def get_layout_str(self, pkg_name = None):
        def _display_time_point(view):
            text = view['text']
            match_result = re.match('((1[0-2]|0?[1-9]):([0-5][0-9]) ?([AaPp][Mm])?)', text)
            return match_result is not None

        def _clean_attrs(i):
            attr_dict = dict(i.attrib)
            if attr_dict['class'] in ['android.widget.EditText', 'android.widget.Switch'] or _display_time_point(attr_dict):
                attr_dict['text'] = ''
            ## !! need to consider all attrs because button with different attribute values might lead to different screen.
            for attr_tb_del in ["checked", "selected", "focused","bounds"]:
                del attr_dict[attr_tb_del]
            return str(attr_dict)

        candidate_pkgs = [pkg_name, "com.google.android.packageinstaller", "com.android.packageinstaller","com.google.android.permissioncontroller"]
        views = self.etree_layout.xpath(
            "//node[@package='{}']".format("' or @package='".join(candidate_pkgs))
        )
        view_strs = [
            _clean_attrs(i)
            for i in views
            if len(i.getchildren()) == 0
        ]
        view_strs.sort()
        layout_str = " ".join(view_strs)
        return layout_str

    def get_layout_hash(self, pkg_name=None):
        return int(hashlib.md5(self.get_layout_str(pkg_name).encode()).hexdigest(), 16)

    def iterate_views(self, app_only=False):
        if app_only:
            leaf_elements = self.etree_layout.xpath("//*[not(*) and @package != 'com.android.systemui' and @package != 'com.google.android.systemui' and @package != 'com.google.android.apps.nexuslauncher' and @package != 'com.android.apps.nexuslauncher']")
        else:
            leaf_elements = self.etree_layout.xpath("//*[not(*)]")
        
        return leaf_elements
    
    def keyboard_on(self):
        keyboard_elements = self.etree_layout.xpath('//node[@resource-id="com.google.android.inputmethod.latin:id/keyboard_holder"]')\
                    + self.etree_layout.xpath('//node[@resource-id="com.android.inputmethod.latin:id/keyboard_view"]')

        return len(keyboard_elements) > 0

# extract the coordinates of bounds from a string in the form of [A,B][C,D]
def parse_view_bounds(loc_str):
    match_result = re.search("\[([-\d]+),([-\d]+)]\[([-\d]+),([-\d]+)]", loc_str)
    if match_result is None:
        raise Exception(f"Error when parsing uiautomator location. {loc_str}")
    dimensions = [int(i) for i in match_result.groups()]
    return dimensions


# determine whether a point is within a view bound
def check_point_within_bound(bounds, tgt_x, tgt_y):
    x_1, y_1, x_2, y_2 = parse_view_bounds(bounds)
    return x_1 < float(tgt_x) < x_2 and y_1 < float(tgt_y) < y_2


# determine whether a bound is within another
def bound_B_in_A(bound_A, bound_B):
    x_1, y_1, x_2, y_2 = parse_view_bounds(bound_B)
    x_a, y_a, x_b, y_b = parse_view_bounds(bound_A)
    return x_1 > x_a and y_1 > y_a and x_2 < x_b and y_2 < y_b


# determine whether a view is in another view
def view_B_in_A(view_A: Tag, view_B: Tag):
    return bound_B_in_A(view_B['bounds'], view_A['bounds'])


# compute the center coordinates of a bound
def get_bound_center(bound):
    x_1, y_1, x_2, y_2 = parse_view_bounds(bound)
    return (x_1 + x_2) // 2, (y_1 + y_2) // 2


viewGroupClasses = ['android.widget.ListView', 'android.widget.GridView']


## determine whether a view is clickable
def is_clickable_view(view):
    return view.attrib['clickable'] == "true" and view.attrib['class'] not in viewGroupClasses and not is_editable_view(
        view)  # scrollable view and editable view is also clickable, so need to filter them

def is_switch(view):
    return view.attrib['class'] in ['android.widget.Switch']

def is_checkbox(view):
    return view.attrib['class'] in ['android.widget.CheckBox']

# determine whether a view is editable
def is_editable_view(view):
    return view.attrib['class'] == "android.widget.EditText"

def is_image_view(view):
    return view.attrib['class'] == 'android.widget.ImageView'

def is_layout_view(view):    
    return view.attrib['class'].endswith("Layout")

# extract the texts from the siblings of a view
def retrieve_text_from_siblings(view: _Element) -> set:
    text_set = set()
    siblings = set(view.itersiblings())
    for sibling in siblings:
        if isinstance(sibling, _Element) and "" != sibling.attrib['text']:
            if is_clickable_view(sibling) or is_editable_view(
                    sibling):  # if the child node is another interactable view, then do not include its text
                continue
            text_set.add(sibling.attrib['text'].strip())
    if view.attrib['text'] != "":
        text_set.add(view.attrib['text'].strip())
    return text_set


# extract the text information from the label sibling of a button (sometimes the text representation of a button is not on itself but on a sibling view)
def retrieve_text_from_text_label_siblings(xml_tag: _Element) -> set:
    def __overlap(inner, outer):
        pass

    ext_set = set()
    siblings = list(filter(lambda x: isinstance(x, _Element), xml_tag.itersiblings()))
    if len(siblings) == 1 and siblings[0].attrib["class"] == "android.widget.TextView" and siblings[0].attrib[
        "clickable"] == "false" and xml_tag.attrib['text'] == "" and xml_tag.attrib['content-desc'] == "" and siblings[0].attrib[
        'text'] != "":
        # likely to be a text label for a FAB button
        ext_set.add(siblings[0].attrib['text'])
    return ext_set


# extract the text information from the children of a view
def retrieve_text_from_children(xml_tag: _Element) -> set:
    text_set = set()
    if xml_tag.attrib['text'] != "":
        text_set.add(xml_tag.attrib['text'].strip())
    for child in xml_tag.iterchildren():
        if isinstance(child, _Element):
            if is_clickable_view(child) or is_editable_view(
                    child):  # if the child node is another interactable view, then do not include its text
                continue
            text_set.update(retrieve_text_from_children(child))
    return text_set


# extract the possible texts related to a view including those from its siblings and children
def get_text_from_view(view: _Element, include_children = True, include_siblings = True) -> list:
    text_set = {view.attrib['text']}
    # if retrieve_text_from_siblings:
    if include_siblings:
        if view.attrib['class'] == 'android.widget.EditText':
            text_set.update(retrieve_text_from_siblings(view))
        else:
            text_set.update(retrieve_text_from_text_label_siblings(view))
    if len(text_set) == 0 or all([i == "" for i in text_set]) or include_children:
        text_set.update(retrieve_text_from_children(view))
    return list(text_set)


# retrieve all the textual representation of a view including: texts from itself and its children, content description and resource id
def get_textual_representation(view: _Element):
    if view is None:
        return []
    texts =  list(set(get_text_from_view(view) + [view.attrib['content-desc']] + [
        view.attrib['resource-id'].split('/')[-1].replace("_", " ").strip()]))
    try:
        texts.remove('')
    except ValueError:
        pass
    texts.sort()
    return texts

def get_resource_id(view:_Element, resolve_case=True):
    def __to_normal_form(string, use_llm=False):
        if use_llm:
            system_msg = "I give you a word and it might be a concatenation of multiple words (by underscores), or in camel case. You need to parse it and return me the normal form of the words. For example, for word addtofavoritesitem, you need to parse it into -- add to favorite item."
            user_msg = string
            response, _ = language_query(user_msg, system_msg, model='gpt-4', seed=10, temperature=0)
            return response
        if '_' in string: # "xx_xx_xx"
            return string.replace('_',' ')
        elif ' ' not in string and not string.islower(): # AnHamburger
            return re.sub(r'(?<!^)(?=[A-Z])', ' ', string)
        return string
    
    res_id = view.attrib['resource-id'].split("/")[-1]
    return __to_normal_form(res_id, False)
    
def get_content_desc(view:_Element):
    return view.attrib['content-desc']
    
def get_prompt_desc_for_view(view:_Element):
    if view is None:
        return ""
    
    type_desc = "other"
    if is_editable_view(view):
        type_desc = "input box"
    elif is_switch(view):
        type_desc = "switch button"
    elif is_checkbox(view):
        type_desc = "checkbox"
    elif is_image_view(view):
        type_desc = "image"
    elif is_clickable_view(view):
        type_desc = "button"
        
    location_desc = "" #
    status_desc = ""
    
    view_text = "".join(get_text_from_view(view)).replace("\n","")
    desc = ""
    desc_attributes = filter(lambda x: x!="",
        [get_resource_id(view, resolve_case=True), get_content_desc(view)])
    desc_txt = "; ".join(desc_attributes)
    
    desc = f"TYPE: {type_desc}. LABEL: {view_text}. DESC: {desc_txt}"
    return desc