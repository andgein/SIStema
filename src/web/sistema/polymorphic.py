import html

import polymorphic.admin


def get_all_inheritors(klass):
    """
    Returns the list of all inheritors of the class
    :return: list of classes
    """
    subclasses = set()
    queue = [klass]
    while queue:
        parent = queue.pop()
        children = {subclass
                    for subclass in parent.__subclasses__()
                    if subclass not in subclasses}
        subclasses.update(children)
        queue.extend(children)
    return list(subclasses)


class PolymorphicParentModelAdmin(polymorphic.admin.PolymorphicParentModelAdmin):
    def get_child_models(self):
        if self.base_model is None:
            raise NotImplementedError('You should define base_model in %s' % self.__class__.__name__)
        inheritors = get_all_inheritors(self.base_model)
        # Remove abstract models
        inheritors = [c for c in inheritors if not c._meta.abstract]
        return inheritors

    def get_class(self, obj):
        return obj.get_real_instance_class().__name__

    get_class.short_description = 'Type'

    def get_real_instance_str(self, obj):
        return str(obj.get_real_instance())

    get_real_instance_str.short_description = 'Description'

    def get_description(self, obj):
        """
        Returns html:
        {get_real_instance_str(obj)}
        <div class="field-get_description-class_name">{get_class(obj)}</div>
        """
        description = self.get_real_instance_str(obj)
        return html.escape(description) + \
               '<div class="field-get_description-class_name">{}</div>'.format(
                   html.escape(self.get_class(obj))
               )

    get_description.short_description = 'Description'
    get_description.allow_tags = True

    class Media:
        css = {
            'all': ('css/admin/polymorphic_parent_model_admin.css',)
        }
