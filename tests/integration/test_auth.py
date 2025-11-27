def test_rota_login_abre(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()


def test_login_funciona(client, usuario_padrao):
    resp = client.post(
        "/login",
        data={"email": "tester@example.com", "senha": "123456"},
        follow_redirects=True,
    )    

    assert resp.status_code == 200
    assert b"dashboard" in resp.data.lower()
    
