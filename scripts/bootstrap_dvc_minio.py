"""Bootstrap a team-scoped DVC bucket/user in the local MinIO lab.
Requires a MinIO port-forward on localhost:19000 and kubectl access.
Secrets stay in temporary mc configuration and ~/.config/ai-platform/dvc.env.
"""
import base64, json, os, secrets, subprocess, tempfile
from pathlib import Path

BUCKET = "ai-platform-dvc"
USER = "dvc-tax-ml-team"
MC = str(Path.home() / ".local/bin/mc")

def main():
    raw = json.loads(subprocess.check_output([
        "kubectl", "-n", "ml-platform", "get", "secret", "minio-credentials", "-o", "json"
    ]))["data"]
    credentials = Path.home() / ".config/ai-platform/dvc.env"
    credentials.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if credentials.exists():
        existing = dict(line.split("=", 1) for line in credentials.read_text().splitlines() if "=" in line)
    password = existing.get("AWS_SECRET_ACCESS_KEY", secrets.token_urlsafe(36))
    with tempfile.TemporaryDirectory(prefix="minio-bootstrap-") as directory:
        def mc(*args):
            return subprocess.run([MC,"--config-dir",directory,*args],check=True,capture_output=True,text=True)
        mc("alias","set","lab","http://127.0.0.1:19000",
           base64.b64decode(raw["MINIO_ROOT_USER"]).decode(),
           base64.b64decode(raw["MINIO_ROOT_PASSWORD"]).decode())
        mc("mb","--ignore-existing",f"lab/{BUCKET}")
        mc("version","enable",f"lab/{BUCKET}")
        policy = {"Version":"2012-10-17","Statement":[
            {"Effect":"Allow","Action":["s3:ListBucket","s3:GetBucketLocation","s3:ListBucketMultipartUploads"],"Resource":[f"arn:aws:s3:::{BUCKET}"]},
            {"Effect":"Allow","Action":["s3:GetObject","s3:PutObject","s3:DeleteObject","s3:AbortMultipartUpload","s3:ListMultipartUploadParts"],"Resource":[f"arn:aws:s3:::{BUCKET}/tax-ml-team/*"]}
        ]}
        policy_file = Path(directory)/"policy.json"
        policy_file.write_text(json.dumps(policy))
        mc("admin","policy","create","lab",USER,str(policy_file))
        mc("admin","user","add","lab",USER,password)
        mc("admin","policy","attach","lab",USER,"--user",USER)
    credentials.write_text(f"AWS_ACCESS_KEY_ID={USER}\nAWS_SECRET_ACCESS_KEY={password}\nAWS_DEFAULT_REGION=us-east-1\n")
    credentials.chmod(0o600)
    print(f"MinIO bucket {BUCKET} ready; team-scoped credentials saved to {credentials}")

if __name__ == "__main__":
    main()
