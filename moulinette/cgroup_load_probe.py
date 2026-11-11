"""Ancien témoin de charge désactivé : aucune allocation forcée ni charge CPU.

Les limites de mémoire ne sont PAS éprouvées par ce module. Déclencher un OOM
nécessite une VM jetable et une méthodologie indépendante ; un scope systemd
utilisateur ne suffit pas à garantir l'absence d'impact sur la session.
"""
import json

def witness_main():
    print(json.dumps({'version':1, 'status':'unavailable',
                      'message':'Témoin de charge désactivé : validation OOM réelle non réalisée.'},
                     ensure_ascii=True), flush=True)

if __name__ == '__main__':
    witness_main()
    raise SystemExit(2)
