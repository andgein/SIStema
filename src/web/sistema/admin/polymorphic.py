import polymorphic.admin

from . import main


class PolymorphicParentModelAdmin(
        main.SistemaAdminMixin,
        polymorphic.admin.PolymorphicParentModelAdmin
):
    def get_child_models(self):
        inheritors = get_all_inheritors(self.base_model)
        # Remove absctract models
        return [c for c in inheritors if not c._meta.abstract]

    def get_class(self, obj):
        return obj.get_real_instance_class().__name__
    get_class.short_description = 'Type'


class PolymorphicChildModelAdmin(main.SistemaAdminMixin,
                                 polymorphic.admin.PolymorphicChildModelAdmin):
    pass


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
