import re
import subprocess
import yaml

rendered = subprocess.check_output(['kubectl', 'kustomize', 'environments/dev'], text=True)
objects = list(yaml.safe_load_all(rendered))
assert {o['kind'] for o in objects} == {'Deployment', 'Service'}
for obj in objects:
    if obj['kind'] != 'Deployment':
        continue
    pod = obj['spec']['template']['spec']
    assert pod['automountServiceAccountToken'] is False
    for container in pod['containers']:
        assert re.fullmatch(r'ghcr\.io/[a-z0-9_.-]+/[a-z0-9_.-]+@sha256:[a-f0-9]{64}', container['image']), 'Set the reviewed application image digest before merging this deployment PR'
        assert container['securityContext']['readOnlyRootFilesystem'] is True
print('Deployment manifest and immutable image validation passed')
