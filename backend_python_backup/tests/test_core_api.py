def test_register_login_me(api, client):
    created = api.register("alice")
    assert created["roles"] == ["player"] and "password_hash" not in created
    _, headers = api.user("bob")
    me = client.get(api.url("/users/me"), headers=headers)
    assert me.status_code == 200 and me.json()["username"] == "bob"


def test_error_envelope(api, client):
    api.register("alice")
    dup = client.post(api.url("/auth/register"), json={
        "email": "ALICE@example.com", "username": "other", "password": "Passw0rdOK",
        "full_name": "X"})
    assert dup.status_code == 409 and dup.json() == {"detail": "Email already registered"}

    bad = client.post(api.url("/auth/register"), json={"email": "nope", "username": "u"})
    assert bad.status_code == 422 and isinstance(bad.json()["detail"], list)

    admin_role = client.post(api.url("/auth/register"), json={
        "email": "a@example.com", "username": "aaa", "password": "Passw0rdOK",
        "full_name": "A", "role": "admin"})
    assert admin_role.status_code == 403

    wrong = client.post(api.url("/auth/login"), json={"email": "alice@example.com", "password": "x"})
    assert wrong.status_code == 401 and wrong.json() == {"detail": "Incorrect email or password"}

    assert client.get(api.url("/users/me")).json() == {"detail": "Not authenticated"}
    assert client.get(api.url("/users/me"), headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.get("/api/v1/does-not-exist").json().get("detail")


def test_rbac_and_admin_lock(api, client):
    _, player = api.user("pat")
    assert client.get(api.url("/admin/users"), headers=player).status_code == 403
    admin = api.make_admin()

    listing = client.get(api.url("/admin/users?q=pat&page_size=5"), headers=admin)
    assert listing.status_code == 200 and listing.json()["total"] == 1

    target = listing.json()["items"][0]["id"]
    locked = client.patch(api.url(f"/admin/users/{target}/status"), json={"is_active": False}, headers=admin)
    assert locked.json()["is_active"] is False
    login = client.post(api.url("/auth/login"), json={"email": "pat@example.com", "password": "Passw0rdOK"})
    assert login.status_code == 403 and login.json() == {"detail": "Account is disabled"}
    assert client.get(api.url("/users/me"), headers=player).status_code == 403  # token now useless

    toggled = client.patch(api.url(f"/admin/users/{target}/status"), json={}, headers=admin)
    assert toggled.json()["is_active"] is True


def test_sports_profiles_availability(api, client):
    admin = api.make_admin()
    sport = client.post(api.url("/sports"), json={"name": "Bóng đá"}, headers=admin)
    assert sport.status_code == 201 and sport.json()["slug"] == "bong-da"
    assert client.post(api.url("/sports"), json={"name": "bóng đá"}, headers=admin).status_code == 409

    _, headers = api.user("pat")
    body = {"sport_id": sport.json()["id"], "position": "ST", "skill_level": "advanced", "city": "Đà Nẵng"}
    profile = client.post(api.url("/player-profiles"), json=body, headers=headers)
    assert profile.status_code == 201
    pid = profile.json()["id"]
    assert client.post(api.url("/player-profiles"), json=body, headers=headers).status_code == 409

    slot = {"day_of_week": 6, "start_time": "08:00", "end_time": "10:00"}
    assert client.post(api.url(f"/player-profiles/{pid}/availability"), json=slot, headers=headers).status_code == 201
    overlap = {"day_of_week": 6, "start_time": "09:00", "end_time": "11:00"}
    assert client.post(api.url(f"/player-profiles/{pid}/availability"), json=overlap, headers=headers).status_code == 422

    _, other = api.user("quinn")
    found = client.get(api.url("/player-profiles?day_of_week=6&available_from=09:00&city=đà nẵng"), headers=other)
    assert found.json()["total"] == 1
    assert client.patch(api.url(f"/player-profiles/{pid}"), json={"bio": "hi"}, headers=other).status_code == 403


def test_notifications(api, client):
    _, headers = api.user("pat")
    assert client.get(api.url("/notifications/unread-count"), headers=headers).json() == {"unread": 1}  # welcome
    nid = client.get(api.url("/notifications"), headers=headers).json()["items"][0]["id"]
    assert client.patch(api.url(f"/notifications/{nid}/read"), headers=headers).json()["is_read"] is True
    assert client.patch(api.url("/notifications/read-all"), headers=headers).json() == {"updated": 0}


def test_chat_websocket(api, client):
    a, ha = api.user("ann")
    b, hb = api.user("ben")
    c, hc = api.user("cat")
    room = client.post(api.url("/chat/rooms"), json={"user_id": b["id"]}, headers=ha)
    assert room.status_code == 201
    rid = room.json()["id"]
    assert client.post(api.url("/chat/rooms"), json={"user_id": b["id"]}, headers=ha).status_code == 200

    tok_a, tok_b = ha["Authorization"].split()[1], hb["Authorization"].split()[1]
    tok_c = hc["Authorization"].split()[1]
    path = api.url(f"/ws/chat/{rid}")
    with client.websocket_connect(f"{path}?token={tok_a}") as wa, \
            client.websocket_connect(f"{path}?token={tok_b}") as wb:
        wa.send_json({"content": "hello ben"})
        assert wa.receive_json()["data"]["content"] == "hello ben"
        assert wb.receive_json()["data"]["sender_id"] == a["id"]
        wb.send_json({"content": "   "})
        assert wb.receive_json()["type"] == "error"

    history = client.get(api.url(f"/chat/rooms/{rid}/messages"), headers=hb)
    assert history.json()["total"] == 1
    assert client.get(api.url(f"/chat/rooms/{rid}/messages"), headers=hc).status_code == 403

    with client.websocket_connect(f"{path}?token={tok_c}") as wc:  # not a member
        try:
            wc.receive_json()
        except Exception as exc:  # starlette raises WebSocketDisconnect with code 4403
            assert getattr(exc, "code", None) == 4403
