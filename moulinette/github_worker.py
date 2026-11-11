"""Témoin fixe lancé par github_bounded dans Bubblewrap ; pas d'API publique."""
import base64
import json
import os
import stat
import sys
from pathlib import Path
from .github_source import GitHubSourceError, trusted_public_repository, MAX_FILE
from .exercise_catalog import EXERCISES


def main():
    try:
        if len(sys.argv) != 5: raise GitHubSourceError('Arguments du superviseur Git invalides.')
        url, exercise, ref, subdir = sys.argv[1:]
        with trusted_public_repository(url, exercise, ref=ref or None, subdir=subdir or None, _allow_unbounded_environment=True) as (stage, source):
            if 'project' in EXERCISES[exercise]:
                files=[];dirs=[]
                for item in sorted(stage.rglob('*')):
                    rel=item.relative_to(stage).as_posix()
                    if item.is_symlink(): raise GitHubSourceError('Lien dans la copie de projet.')
                    if item.is_dir(): dirs.append(rel)
                    elif item.is_file(): files.append({'path':rel,'data_b64':base64.b64encode(item.read_bytes()).decode('ascii')})
                    else: raise GitHubSourceError('Type de fichier projet non pris en charge.')
                response={'version':2,'files':files,'dirs':dirs,'source':source}
                print(json.dumps(response,ensure_ascii=True,separators=(',',':')),flush=True)
                return
            name = EXERCISES[exercise]['source']
            entries = sorted(os.listdir(stage))
            kind='absent'; content=b''
            if name in entries:
                info=(stage/name).lstat()
                if stat.S_ISLNK(info.st_mode): kind='symlink'
                elif stat.S_ISDIR(info.st_mode): kind='dir'
                elif stat.S_ISREG(info.st_mode):
                    kind='file'
                    with (stage/name).open('rb') as f: content=f.read(MAX_FILE+2)
                    if len(content)>MAX_FILE+1: raise GitHubSourceError('Copie de source incohérente.')
                else: raise GitHubSourceError('Type de source non pris en charge.')
            response={'version':1, 'entries':entries, 'source_type':kind,
                      'source_b64':base64.b64encode(content).decode('ascii'), 'source':source}
    except (GitHubSourceError, OSError, ValueError) as exc:
        response={'version':1,'error':str(exc)[:500]}
    print(json.dumps(response,ensure_ascii=True,separators=(',',':')),flush=True)

if __name__ == '__main__': main()
