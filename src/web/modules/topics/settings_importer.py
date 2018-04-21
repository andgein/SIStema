import importlib
import importlib.util
import importlib.machinery
import os
import os.path
import sys

import itertools

from django.db import transaction

from . import models
import modules.entrance.models
from modules.topics.models import levels

r"""
Example of running

import modules.topics.models as models
q = models.TopicQuestionnaire.objects.get()
import modules.topics.settings_importer as si
importer = si.CitxxSettingsImporter(q)
importer.import_settings_from_config(r'<path-to>/sis-entry-exam-proto/www/config')
"""


class SettingsImporter:
    def __init__(self, questionnaire):
        self.questionnaire = questionnaire

    # See http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path for details
    @staticmethod
    def import_module_by_filename(module_name, file_name):
        # TODO: not worked in Python 3.5
        if sys.version_info[:2] >= (3, 6):
            spec = importlib.util.spec_from_file_location(module_name, file_name)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        module = importlib.machinery.SourceFileLoader(module_name, file_name).load_module()
        return module

    # TODO: reset AutoFields to zero as option
    def clear(self):
        # Remove all levels, levels downward & upward dependencies, topics and so on
        # because topics has foreign key to level
        models.Level.objects.filter(questionnaire=self.questionnaire).delete()

        # Remove all scales, scale labels and so on
        models.Scale.objects.filter(questionnaire=self.questionnaire).delete()

        # Remove all tags
        models.Tag.objects.filter(questionnaire=self.questionnaire).delete()

        # DANGEROUS: remove all entrance levels
        modules.entrance.models.EntranceLevel.objects.filter(school=self.questionnaire.school).delete()


# Importer for config files form topic-questionnaire-system prototype by Artem Tabolin and Irina Brovar
# TODO add logging
class CitxxSettingsImporter(SettingsImporter):
    def import_levels(self, path):
        """
        Imports from config in follow format:
            levels = ['E', 'D', 'Cprime', 'C', 'Bprime', 'B', 'Aprime', 'A', 'Z', 'Max']

            downward_dependencies = [
                ('Max', 70, 'A'),
                ('Z', 75, 'A'),
                ...
            ]

            upward_dependencies = [
                ('E', 45, 'C'),
                ('D', 70, 'C'),
                ...
            ]
        """
        module = self.import_module_by_filename('levels', path)

        for level_name in module.levels:
            models.Level(questionnaire=self.questionnaire, name=level_name).save()

        levels_by_name = {l.name: l for l in models.Level.objects.all()}

        for src, percent, dst in module.downward_dependencies:
            models.LevelDownwardDependency(questionnaire=self.questionnaire,
                                           source_level=levels_by_name[src],
                                           destination_level=levels_by_name[dst],
                                           min_percent=percent).save()

        for src, percent, dst in module.upward_dependencies:
            models.LevelUpwardDependency(questionnaire=self.questionnaire,
                                         source_level=levels_by_name[src],
                                         destination_level=levels_by_name[dst],
                                         min_percent=percent).save()

    def import_scales(self, path):
        """
        Imports from config in follow format:
            values_count = 3
            caption = "Практика"
            labels = {
                "algorithm": [
                    "Ни разу не написал рабочую реализацию алгоритма",
                    "Пару раз написал рабочую реализацию алгоритма",
                    "Много раз реализовал алгоритм, могу прямо сейчас сесть и написать"
                ],
                "simple": [
                    "Ни разу не использовал в своих программах",
                    "Использовал пару раз",
                    "Использовал много раз"
                ],
                ...
            }
        """
        for file_name in os.listdir(path):
            if os.path.isdir(os.path.join(path, file_name)):
                continue
            scale_name = os.path.splitext(file_name)[0]

            scale_module = self.import_module_by_filename('scales.%s' % scale_name, os.path.join(path, file_name))
            scale = models.Scale(questionnaire=self.questionnaire,
                                 short_name=scale_name,
                                 title=scale_module.caption,
                                 count_values=scale_module.values_count)
            scale.save()

            # Import label groups
            for group_name, group_labels in scale_module.labels.items():
                label_group = models.ScaleLabelGroup(scale=scale,
                                                     short_name=group_name)
                label_group.save()

                # Save each label in group
                for mark, label in enumerate(group_labels):
                    models.ScaleLabel(group=label_group,
                                      mark=mark,
                                      label_text=label).save()

    def import_topics(self, path):
        """
        Imports from config in follow format:
            import ta_entry

            header = "Одномерные массивы"
            entry_type = ta_entry.TYPE_THEME
            info = {
                "text": "Одномерные массивы (array, vector, list)"
            }
            scales = [("practice3", "simple")]

            questions = []

            dependencies = [
                ("1d_arrays", "practice3", "loops", "practice3", ta_entry.KNOW)
            ]

            level = 'E'

            tags = ['for-cprime-base', 'for-c-base']

        :param path: path to directory with topics' .py files
        """
        for file_name in os.listdir(path):
            if os.path.isdir(os.path.join(path, file_name)):
                continue

            topic_name = os.path.splitext(file_name)[0]
            topic_module = self.import_module_by_filename('topics.%s' % topic_name, os.path.join(path, file_name))

            # Ignore some strange entries: check, result and others
            if topic_module.entry_type != 'theme':
                continue

            topic = models.Topic(questionnaire=self.questionnaire,
                                 short_name=topic_name,
                                 title=topic_module.header,
                                 text=topic_module.info['text'],
                                 level=models.Level.objects.filter(name=topic_module.level).get())
            topic.save()

            # Import tags
            for tag_name in topic_module.tags:
                tag, _ = models.Tag.objects.get_or_create(questionnaire=self.questionnaire,
                                                          short_name=tag_name, defaults={'title': tag_name})
                topic.tags.add(tag)

            # Import scales
            # TODO BUG: add questionnaire filters
            for scale_name, label_group_name in topic_module.scales:
                label_group = models.ScaleLabelGroup.objects.filter(scale__short_name=scale_name,
                                                                    short_name=label_group_name).get()
                models.ScaleInTopic(topic=topic,
                                    scale_label_group=label_group).save()

        # TODO: optimize second step
        # Second step: make dependencies
        for file_name in os.listdir(path):
            if os.path.isdir(os.path.join(path, file_name)):
                continue

            topic_name = os.path.splitext(file_name)[0]
            topic_module = self.import_module_by_filename('topics.%s' % topic_name, os.path.join(path, file_name))

            # Ignore some strange entries: check, result and others
            if topic_module.entry_type != 'theme':
                continue

            # Import topic dependencies
            for src_topic, src_scale, dst_topic, dst_scale, function_matrix in topic_module.dependencies:
                scales_in_source_topic = models.ScaleInTopic.objects.filter(topic__short_name=src_topic,
                                                                            scale_label_group__scale__short_name=src_scale)
                scales_in_destination_topic = models.ScaleInTopic.objects.filter(topic__short_name=dst_topic,
                                                                                 scale_label_group__scale__short_name=dst_scale)
                for source, destination in itertools.product(scales_in_source_topic, scales_in_destination_topic):
                    # Create TopicDependency record for each possible pair (source_mark, destination_mark)
                    for source_mark, destination_marks in function_matrix.items():
                        for destination_mark in destination_marks:
                            models.TopicDependency(source=source,
                                                   destination=destination,
                                                   source_mark=source_mark,
                                                   destination_mark=destination_mark).save()
                            # Automatically add reversed dependency
                            models.TopicDependency(source=destination,
                                                   destination=source,
                                                   source_mark=destination_mark,
                                                   destination_mark=source_mark).save()

    def import_order(self, path):
        """
        Imports from config in follow format:
            entries = [
                'if',
                'loops',
                ...
            ]
        """
        order_module = self.import_module_by_filename('order', path)
        for order, topic_name in enumerate(order_module.entries):
            topic = models.Topic.objects.filter(questionnaire=self.questionnaire,
                                                short_name=topic_name).get()
            topic.order = order
            topic.save()

    def import_requirements(self, path):
        result_module = self.import_module_by_filename('result', path)
        order = 0
        for entrance_level, requirements in result_module.group_requirements:
            order += 1
            level = modules.entrance.models.EntranceLevel(school=self.questionnaire.school,
                                                          short_name=entrance_level.lower(),
                                                          name=entrance_level,
                                                          order=order)
            level.save()

            for tag, max_penalty in requirements:
                levels.EntranceLevelRequirement(questionnaire=self.questionnaire,
                                                entrance_level=level,
                                                tag=models.Tag.objects.filter(questionnaire=self.questionnaire,
                                                                              short_name=tag).get(),
                                                max_penalty=max_penalty).save()


    def import_settings_from_config(self, config_path):
        self.clear()

        with transaction.atomic():
            levels_path = os.path.join(config_path, 'levels.py')
            self.import_levels(levels_path)

            scales_path = os.path.join(config_path, 'scales')
            self.import_scales(scales_path)

            topics_path = os.path.join(config_path, 'entries')
            # Prepare: load module ta_entry which are using in topics declarations
            self.import_module_by_filename('ta_entry', os.path.join(config_path, 'ta_entry.py'))
            self.import_topics(topics_path)

            self.import_order(os.path.join(config_path, 'sort_order.py'))

            self.import_requirements(os.path.join(topics_path, 'result.py'))
