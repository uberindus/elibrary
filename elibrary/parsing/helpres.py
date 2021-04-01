def find_and_get(root, rel_path):
    tag = root.find(rel_path)
    return None if tag == None else tag.text


def get_plain_text(str):
    import re
    reg = r'(&lt;sub&gt;|&lt;/sub&gt;|&lt;sup&gt;|&lt;/sup&gt;|&lt;b&gt;|&lt;/b&gt;|&lt;i&gt;|&lt;/i&gt;|&lt;br&gt;|&lt;/br&gt;\
    |<sub>|</sub>|<sup>|</sup>|<b>|</b>|<i>|</i>|<br>|</br>)'
    return re.sub(reg, "", str)
