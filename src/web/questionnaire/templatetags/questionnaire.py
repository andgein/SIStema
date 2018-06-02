from django import template

register = template.Library()


@register.simple_tag
def is_block_visible_to_user(questionnaire_block, user):
    return questionnaire_block.is_visible_to_user(user)
