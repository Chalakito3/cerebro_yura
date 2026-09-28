import json, base64, time, urllib.request as u
WD="http://127.0.0.1:4445"; APP="http://127.0.0.1:5051"
def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = u.Request(WD+path, data=data, method=method, headers={"Content-Type":"application/json"})
    try:
        return json.loads(u.urlopen(req, timeout=120).read())["value"]
    except u.HTTPError as e:
        raise RuntimeError(e.read().decode())
def setfake(**kw):
    req = u.Request(APP+"/__test/set", data=json.dumps(kw).encode(), method="POST", headers={"Content-Type":"application/json"})
    u.urlopen(req).read()
class S:
    def __init__(self):
        v = call("POST","/session",{"capabilities":{"alwaysMatch":{"browserName":"firefox","moz:firefoxOptions":{"args":["-headless"],"prefs":{"intl.accept_languages":"es"}}}}})
        self.id = v["sessionId"]
    def size(self,w,h):
        call("POST",f"/session/{self.id}/window/rect",{"width":w,"height":h})
        # ajustar viewport real
        iw, ih = self.js("return [innerWidth, innerHeight]")
        call("POST",f"/session/{self.id}/window/rect",{"width":w+(w-iw),"height":h+(h-ih)})
    def go(self,url): call("POST",f"/session/{self.id}/url",{"url":url})
    def js(self,s,args=None): return call("POST",f"/session/{self.id}/execute/sync",{"script":s,"args":args or []})
    def shot(self,path, full=False):
        v = call("GET",f"/session/{self.id}/moz/screenshot/full" if full else f"/session/{self.id}/screenshot")
        open(path,"wb").write(base64.b64decode(v))
    def quit(self): call("DELETE",f"/session/{self.id}")
