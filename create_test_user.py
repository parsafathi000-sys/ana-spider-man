"""create_test_user.py — automated verification of the VLESS connection flow.

Requirements proven:
  1. New user gets a STANDARD dashed UUID4 (no 32-hex form).
  2. The user's config_uuid is registered as an Xray client in the generated
     config.json (so the link actually connects).
  3. The subscription /sub/{uuid} returns a valid vless:// link whose UUID
     matches the Xray client id.
  4. ws/tls link path is /ws/{inbound_id} and matches the server wsSettings.

Run:  python3 create_test_user.py   (inside the project, with a temp HERMES-free
env; uses a stub Xray binary so no real Xray is required for the logic check).
"""
import sys, os, tempfile, asyncio, uuid as _uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import services.xray_service as xs


def _make_stub_xray(path: str):
    with open(path, "w") as f:
        f.write("#!/bin/sh\nif [ \"$1\" = \"version\" ]; then echo \"Xray 26.3.27 (test)\"; exit 0; fi\nexit 0\n")
    os.chmod(path, 0o755)
    return path


async def main():
    # Isolated temp state so we don't touch any real data.
    state = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    state.write("{}")
    state.close()
    os.environ["SPIDER_STATE_FILE"] = state.name
    os.environ["XRAY_CONFIG_PATH"] = tempfile.mktemp(suffix=".json")

    stub = tempfile.NamedTemporaryFile(suffix="", delete=False)
    stub.close()
    xs.XRAY_BINARY_PATH = _make_stub_xray(stub.name)
    async def _installed():
        return True
    xs.is_xray_installed = _installed

    from fastapi.testclient import TestClient
    import main
    client = TestClient(main.app)

    passed = failed = 0
    def check(name, cond, detail=""):
        nonlocal passed, failed
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}  {'' if cond else detail}")
        if cond:
            passed += 1
        else:
            failed += 1

    # 1) Create a ws/tls inbound
    ib = client.post("/api/inbounds", json={
        "name": "WS-TLS", "protocol": "vless", "port": 1234,
        "external_port": 29362, "external_domain": "reseau.proxy.rlwy.net",
        "network": "ws", "security": "tls", "domain": "reseau.proxy.rlwy.net",
        "sni": "reseau.proxy.rlwy.net", "fingerprint": "chrome",
        "ws_settings": {"path": "", "host": ""},
    })
    check("inbound created 200", ib.status_code == 200, ib.text[:160])
    iid = ib.json().get("inbound_id")

    # 2) Create a user
    r = client.post("/api/users", json={
        "username": "testuser", "traffic_limit_gb": 10,
        "expire_days": 30, "inbound_id": iid,
    })
    check("user created 200", r.status_code == 200, r.text[:160])
    uid = r.json().get("user_id")

    # 3) DB UUID is standard dashed format
    from core.state import USERS
    u = USERS.get(uid, {})
    cuuid = u.get("config_uuid")
    HEX32 = __import__("re").compile(r"^[0-9a-fA-F]{32}$")
    check("config_uuid is NOT 32-hex", not HEX32.match(str(cuuid)), str(cuuid))
    check("config_uuid is dashed UUID4",
          str(_uuid.UUID(str(cuuid))) == str(cuuid), str(cuuid))

    # 4) Xray client exists in generated config with that id
    cfg = xs.generate_xray_server_config()
    client_ids = []
    for cin in cfg.get("inbounds", []):
        for c in cin.get("settings", {}).get("clients", []):
            client_ids.append(c.get("id"))
    check("Xray client id == config_uuid", cuuid in client_ids,
          f"{cuuid} not in {client_ids}")

    # 5) Subscription /sub/{uuid} returns a vless link with that UUID
    ru = client.get("/api/users")
    sub_uuid = next(x["uuid"] for x in ru.json()["users"] if x["username"] == "testuser")
    rs = client.get(f"/sub/{sub_uuid}", headers={"Accept": "*/*"})
    check("sub returns text/plain", rs.headers.get("content-type", "").startswith("text/plain"), rs.headers.get("content-type"))
    link = rs.text.strip()
    check("sub link starts with vless://", link.startswith("vless://"), link[:80])
    check("sub link UUID == config_uuid", link.split("://", 1)[1].split("@", 1)[0] == cuuid,
          link[:80])

    # 6) ws path is /ws/{inbound_id} and matches server wsSettings
    import urllib.parse as up
    q = dict(up.parse_qsl(up.urlparse(link).query))
    server_ws = None
    for cin in cfg["inbounds"]:
        if cin.get("tag") == f"inbound-{iid}":
            server_ws = cin["streamSettings"]["wsSettings"]["path"]
    check("client ws path == server ws path", q.get("path") == server_ws,
          f"{q.get('path')} vs {server_ws}")

    print(f"\nRESULT: {passed} passed, {failed} failed")
    # cleanup
    for p in (state.name, os.environ["XRAY_CONFIG_PATH"], stub.name):
        try: os.remove(p)
        except OSError: pass
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
