from moulinette.exercise_catalog import EXERCISES

def successful_report(exercise):
    names = ['Fichiers attendus', 'Compilation', 'Prototype et liaison', 'Norminette adaptée']
    names.extend('Test ' + case[0] for case in EXERCISES[exercise]['cases'])
    checks = [{'name': name, 'status': 'pass', 'message': 'ok'} for name in names]
    checks.append({'name': 'Fonctions externes', 'status': 'info', 'message': 'analysé'})
    return {'exercise':'42/c/' + exercise, 'result':'passed', 'checks':checks}
