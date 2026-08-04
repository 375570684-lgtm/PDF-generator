import pytest

from app import app as flask_app


@pytest.fixture()
def client():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        yield client


def test_index_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Homework Helper" in resp.data


def test_upload_with_pasted_text_redirects_to_results(client):
    resp = client.post("/upload", data={
        "homework_text": "1. Solve for x: 3x + 5 = 2x + 20\n2. Write an essay about your summer.",
    })
    assert resp.status_code == 302
    assert "/results/" in resp.headers["Location"]

    results_resp = client.get(resp.headers["Location"])
    assert results_resp.status_code == 200
    assert b"Linear Equation" in results_resp.data
    assert b"Essay" in results_resp.data


def test_upload_with_no_input_shows_error(client):
    resp = client.post("/upload", data={"homework_text": ""})
    assert resp.status_code == 200
    assert b"couldn" in resp.data.lower()


def test_missing_results_session_returns_404(client):
    resp = client.get("/results/does-not-exist")
    assert resp.status_code == 404
