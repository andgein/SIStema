from django.template import Library, Node, TemplateSyntaxError, NodeList

import groups


register = Library()


class IfInGroupNode(Node):
    child_nodelists = ('nodelist_true', 'nodelist_false')

    def __init__(self, user, group_name, nodelist_true, nodelist_false):
        self.user = user
        self.group_name = group_name
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def __repr__(self):
        return "<IfInGroupNode>"

    def render(self, context):
        # TODO (andgein): make tag usefull for system-wide group,
        # not for school-specific ones only
        school = context['request'].school
        if self.user is None:
            user = context['request'].user
        else:
            user = self.user.resolve(context, True)
        group_name = self.group_name.resolve(context, True)
        if groups.is_user_in_group(user, group_name, school):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)


@register.tag
def ifingroup(parser, token):
    bits = list(token.split_contents())
    if not (2 <= len(bits) <= 3):
        raise TemplateSyntaxError("%r takes one or two arguments" % bits[0])

    end_tag = 'end' + bits[0]
    nodelist_true = parser.parse(('else', end_tag))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((end_tag,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()

    if len(bits) == 2:
        user = None
        group = parser.compile_filter(bits[1])
    elif len(bits) == 3:
        user = parser.compile_filter(bits[1])
        group = parser.compile_filter(bits[2])
    else:
        raise ValueError()

    return IfInGroupNode(user, group, nodelist_true, nodelist_false)
