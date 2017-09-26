#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import csv
import sys

import schools.models
import modules.study_results.models as study_models

"""
Tool for moving the study results from csv, both summer and winter, and creating
parallels for winter.

Usage from manage.py shell:
    from tools.migrate_results import populate_study_results
    populate_study_results('2016.winter', 'winter_results.csv')
    populate_study_results('2016', 'july_results.csv')

Was also supposed to work from cmd, but doesn't because of virtual env for django
"""

COMMENT_TYPE_MAP = {
    r'Комментарий по учебе': study_models.StudyComment,
    r'Комментарий по внеучебной деятельности': study_models.SocialComment,
    r'Брать ли в зиму': study_models.AsWinterParticipantComment,
    r'Куда брать в следующем году': study_models.NextYearComment,
    r'Брать ли препом': study_models.AsTeacherComment,
    r'Комментарий для зачисления школьником': study_models.AfterWinterComment,
}


def preprocess_mark(mark):
    mark = mark.strip()
    if mark == '' or mark == r'уехал' or mark == r'уехала':
        mark = 'N/A'
    return study_models.StudyResult.Evaluation.values[mark]


def get_parallel_from_group(group, school):
    parallel = group[0].lower()
    if parallel == 'c':
        if group[1] in '123':
            parallel = 'c.python'
        elif group[1] in '56':
            parallel = 'c.cplusplus'
    if int(group[1]) >= 7:
        parallel += '_prime'
    print(parallel, end=' ', flush=True)
    return schools.models.Parallel.objects.get(short_name=parallel,
                                               school=school)


def get_parallel(parallel, school):
    base = parallel[0].lower()
    ind = 1
    if parallel[ind] == "'":
        base += '_prime'
        ind += 1
    if parallel[ind] == '+':
        base += '_winter'
    print(base, end=' ', flush=True)
    return schools.models.Parallel.objects.get_or_create(short_name=base,
            school=school, name=parallel)


# School short name, csv file
def populate_study_results(school, input_file):
    school = schools.models.School.objects.get(short_name=school)
    csv_file = open(input_file, 'r')
    reader = csv.reader(csv_file, delimiter=',', quotechar='"')
    headers = next(reader)
    print(headers)
    i = 0
    for row in reader:
        i += 1
        print(i, end=' ', flush=True)
        column = {}
        for header, value in zip(headers, row):
            column[header] = value

        school_participant, _ = (schools.models.SchoolParticipant.objects
            .get_or_create(user_id=column['sis_id'], school=school))
        if column.get(r'Группа'):
            school_participant.parallel = get_parallel_from_group(
                column[r'Группа'], school)
        if column.get(r'Параллель'):
            school_participant.parallel, _ = get_parallel(
                column[r'Параллель'], school)
        school_participant.save()
        study_result, _ = study_models.StudyResult.objects.get_or_create(
            school_participant=school_participant)
        study_result.theory = preprocess_mark(column[r'Теория'])
        study_result.practice = preprocess_mark(column[r'Практика'])
        study_result.save()
        for name, comment_class in COMMENT_TYPE_MAP.items():
            if column.get(name):
                comment_class.objects.get_or_create(
                    study_result=study_result,
                    comment=column[name],
                )

    for header in headers:
        print(column[header])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Migrate study results to SIStema')
    parser.add_argument('--input_file', help='file for parsing in csv format')
    parser.add_argument(
        '--school', type=str,
        help='short name of school, i.e. 2016 or 2016.winter')
    args = parser.parse_args(sys.argv[1:])
    populate_study_results(**args)
