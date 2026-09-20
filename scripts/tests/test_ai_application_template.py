"""Golden-path contracts and rendered release guardrails; no external mutations."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml
from jinja2 import Environment, StrictUndefined

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'services/backstage/templates/ai-application'

def render(destination):
    env = Environment(variable_start_string='${{', variable_end_string='}}', undefined=StrictUndefined)
    env.filters['dump'] = json.dumps
    values = dict(name='reviewed-demo', githubOwner='nolet7', description='A quoted "AI" application', reviewer='independent-reviewer', team='tax-ml-team', repoName='reviewed-demo')
    for source in TEMPLATE.rglob('*'):
        if not source.is_file() or source.name == 'template.yaml':
            continue
        relative = source.relative_to(TEMPLATE)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        text = source.read_text()
        if '.github/workflows/' not in relative.as_posix():
            text = env.from_string(text).render(values=values)
        target.write_text(text)

class GoldenApplicationTest(unittest.TestCase):
    def test_only_governance_is_published_to_main(self):
        template = yaml.safe_load((TEMPLATE / 'template.yaml').read_text())
        steps = template['spec']['steps']
        publishers = [s for s in steps if s['action'] == 'publish:github']
        self.assertEqual(len(publishers), 2)
        for step in publishers:
            self.assertTrue(step['input']['sourcePath'].startswith('bootstrap-'))
            self.assertFalse(step['input']['allowAutoMerge'])
        gates = [i for i, s in enumerate(steps) if s['action'] == 'platform:github:require-review']
        prs = [i for i, s in enumerate(steps) if s['action'] == 'publish:github:pull-request']
        self.assertEqual(len(gates), 2)
        self.assertEqual(len(prs), 2)
        self.assertLess(max(gates), min(prs))
        files = {p.relative_to(TEMPLATE / 'bootstrap').as_posix() for p in (TEMPLATE / 'bootstrap').rglob('*') if p.is_file()}
        self.assertEqual(files, {'README.md', 'catalog-info.yaml', '.github/CODEOWNERS'})

    def test_rendered_application_and_deployment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); render(root)
            for f in root.rglob('*.yaml'):
                list(yaml.safe_load_all(f.read_text()))
            catalog = yaml.safe_load((root/'application/catalog-info.yaml').read_text())
            self.assertEqual(catalog['metadata']['description'], 'A quoted "AI" application')
            workflow = (root/'application/.github/workflows/application-ci.yaml').read_text()
            self.assertIn('${{ secrets.GITHUB_TOKEN }}', workflow)
            self.assertIn("github.event_name == 'push'", workflow)
            deployment = root/'deployment'
            # Release PR is deliberately blocked until an actual immutable image is selected.
            rejected = subprocess.run(['python3','scripts/validate.py'],cwd=deployment,capture_output=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn(b'Set the reviewed application image digest', rejected.stderr)
            manifest = deployment/'base/deployment.yaml'
            manifest.write_text(manifest.read_text().replace('REPLACE_WITH_REVIEWED_DIGEST','a'*64))
            subprocess.run(['python3','scripts/validate.py'],cwd=deployment,check=True,capture_output=True)
            onboarding = list(yaml.safe_load_all((deployment/'platform-onboarding.yaml').read_text()))
            self.assertEqual(onboarding[1]['spec']['source']['targetRevision'], 'main')
            self.assertEqual(onboarding[0]['spec']['clusterResourceWhitelist'], [])

if __name__ == '__main__':
    unittest.main()
