"""Configure Backstage's Keycloak client and lab Kubernetes Secrets without printing them."""
import base64,json,secrets,subprocess,urllib.request,urllib.parse
BASE="http://127.0.0.1:19084"
REALM="ai-platform"
ORIGIN="https://backstage.127.0.0.1.nip.io"
def kubectl(*args, payload=None):
    return subprocess.check_output(["kubectl",*args],input=json.dumps(payload).encode() if payload else None)
def secret(namespace,name):
    return json.loads(kubectl("-n",namespace,"get","secret",name,"-o","json"))["data"]
def apply(name,data):
    kubectl("apply","-f","-",payload={"apiVersion":"v1","kind":"Secret","metadata":{"name":name,"namespace":"ai-platform"},"type":"Opaque","stringData":data})
def call(path,token,payload=None,method=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(payload).encode() if payload else None,headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method=method)
    with urllib.request.urlopen(req) as r:
        body=r.read();return json.loads(body) if body else None
root=secret("security","keycloak-bootstrap-admin")
form=urllib.parse.urlencode({"client_id":"admin-cli","grant_type":"password","username":base64.b64decode(root["KC_BOOTSTRAP_ADMIN_USERNAME"]).decode(),"password":base64.b64decode(root["KC_BOOTSTRAP_ADMIN_PASSWORD"]).decode()}).encode()
with urllib.request.urlopen(BASE+"/realms/master/protocol/openid-connect/token",data=form) as r: token=json.load(r)["access_token"]
clients=call(f"/admin/realms/{REALM}/clients",token)
client=next((c for c in clients if c["clientId"]=="backstage"),None)
config={"clientId":"backstage","name":"AI Platform Backstage","enabled":True,"protocol":"openid-connect","publicClient":False,"standardFlowEnabled":True,"directAccessGrantsEnabled":False,"redirectUris":[ORIGIN+"/api/auth/oidc/handler/frame"],"webOrigins":[ORIGIN]}
if client:
    config={**client,**config};call(f"/admin/realms/{REALM}/clients/{client['id']}",token,config,"PUT")
else:
    call(f"/admin/realms/{REALM}/clients",token,config,"POST")
client=next(c for c in call(f"/admin/realms/{REALM}/clients",token) if c["clientId"]=="backstage")
oidc=call(f"/admin/realms/{REALM}/clients/{client['id']}/client-secret",token)["value"]
try: old={k:base64.b64decode(v).decode() for k,v in secret("ai-platform","backstage-secrets").items()}
except subprocess.CalledProcessError: old={}
apply("backstage-secrets",{
    "GITHUB_TOKEN":subprocess.check_output(["gh","auth","token"]).decode().strip(),
    "AUTH_OIDC_CLIENT_SECRET":oidc,
    "AUTH_SESSION_SECRET":old.get("AUTH_SESSION_SECRET",secrets.token_urlsafe(48)),
    "POSTGRES_PASSWORD":old.get("POSTGRES_PASSWORD",secrets.token_urlsafe(36)),
})
ca=secret("cert-manager","ai-platform-root-ca")
cert=base64.b64decode(ca.get("ca.crt",ca["tls.crt"])).decode()
kubectl("apply","-f","-",payload={"apiVersion":"v1","kind":"ConfigMap","metadata":{"name":"backstage-ca","namespace":"ai-platform"},"data":{"ca.crt":cert}})
from pathlib import Path
ca_path=Path.home()/".config/ai-platform/ca.crt";ca_path.parent.mkdir(parents=True,exist_ok=True);ca_path.write_text(cert)
print("Configured Backstage OIDC, runtime credentials and CA trust")
