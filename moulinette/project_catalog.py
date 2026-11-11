"""Construction de descriptions de projets du catalogue expérimental."""

def project_spec(source,version,cfg):
    # Le lanceur cgroup attend les noms de tests au niveau du catalogue.
    cases=[(c['label'], c.get('argv',[]), c['expected']) for c in cfg['cases']]
    return {'source':source,'subject_version':version,'cases':cases,'project':cfg}
