# Script for making submissions archive for cheating review

def collect_solutions(school_short_name, group_short_name):
    """
    Copy all the solutions to "submissions" directory and rename to the
    "<solution_id>-<user_id>-<task_id>.<lang>" format.
    :param school_short_name: Short name of the school to take solutions from
    :param group_short_name: Collect solutions only for users from this group
    """
    from modules.entrance import models  
    import groups.models 
    import shutil  
    import os 
    group = groups.models.AbstractGroup.objects.get(school__short_name=school_short_name, short_name=group_short_name) 
    solutions = models.ProgramEntranceExamTaskSolution.objects.filter(task__exam__school__short_name=school_short_name, user_id__in=group.user_ids) 
    total = solutions.count() 
    lang_to_suffix = { 
        'kumir2': 'kum',  
        'vbnc': 'bas',  
        'csharp': 'cs', 
        'pascal_abc': 'pas',  
        'python3': 'py', 
        'php': 'php',  
        'ruby': 'rb', 
        'java': 'java', 
        'python2': 'py', 
        'gnu_cpp': 'cpp',  
        'gnu_c': 'c', 
        'fpc': 'pas',  
    } 
    SUBMISSIONS_DIR = 'submissions' 
    if not os.path.exists(SUBMISSIONS_DIR): 
        os.makedirs(SUBMISSIONS_DIR) 
    missing = [] 
    for solution in solutions: 
        solution_path = solution.solution 
        print(solution_path, '{}-{}-{}.{}'.format(solution.id, solution.user_id, solution.task_id, lang_to_suffix[solution.language.short_name])) 
        try:    
            shutil.copy(solution_path, '{}/{}-{}-{}.{}'.format(SUBMISSIONS_DIR, solution.id, solution.user_id, solution.task_id, lang_to_suffix[solution.language.short_name])) 
        except:
            print('fail') 
            missing.append(solution_path) 
    print('Missing files:', len(missing))
    print(*missing, sep='\n') 

def make_solutions_csv(school_short_name, group_short_name):
    """
    Get metadata for the solutions and write it to the "solutions.csv" file.
    :param school_short_name: Short name of the school to take solutions
        metadata from
    :param group_short_name: Collect solutions metadata only for users from
        this group
    """
    from modules.entrance import models
    import modules.ejudge.models as ejudge_models
    import groups.models
    import csv
    from django.core.paginator import Paginator
    group = groups.models.AbstractGroup.objects.get(school__short_name=school_short_name, short_name=group_short_name)
    solutions_paginator = Paginator(
        models.ProgramEntranceExamTaskSolution.objects
        .filter(task__exam__school__short_name=school_short_name, user_id__in=group.user_ids)
        .order_by('id')
        .select_related('user__profile', 'user', 'task', 'ejudge_queue_element__submission__result'),
        1000)
    lang_to_suffix = {
        'kumir2': 'kum',
        'vbnc': 'bas',
        'csharp': 'cs',
        'pascal_abc': 'pas',
        'python3': 'py',
        'php': 'php',
        'ruby': 'rb',
        'java': 'java',
        'python2': 'py',
        'gnu_cpp': 'cpp',
        'gnu_c': 'c',
        'fpc': 'pas',
    }
    with open('solutions.csv', 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['solution_id', 'user_id', 'user_name', 'city', 'school', 'task_id', 'task_title', 'language', 'suffix', 'time', 'status', 'test', 'ip'])
        for page_idx in range(1, solutions_paginator.num_pages):
            print('.', end='')
            for solution in solutions_paginator.page(page_idx).object_list:
                if solution.ejudge_queue_element.submission is not None:
                    writer.writerow([
                        solution.id,
                        solution.user_id,
                        solution.user.get_full_name(),
                        solution.user.profile.city,
                        solution.user.profile.school_name,
                        solution.task_id,
                        solution.task.title,
                        solution.language.short_name,
                        lang_to_suffix[solution.language.short_name],
                        solution.created_at,
                        ejudge_models.CheckingResult.Result.get_choice(solution.ejudge_queue_element.submission.result.result).label,
                        solution.ejudge_queue_element.submission.result.failed_test,
                        solution.ip,
                    ])
            print()
