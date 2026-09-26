from pathlib import Path

from web.app import app


def test_example_cards_are_quechua_only_and_not_stale():
    js_path = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'app.js'
    js_text = js_path.read_text(encoding='utf-8')

    assert 'Rimaykullayki' in js_text
    assert "/api/card" in js_text
    assert 'Buenas tardes' not in js_text
    assert 'Gracias por tu ayuda' not in js_text
    assert 'Buen día para aprender' not in js_text
    assert 'Allin p' not in js_text or 'unchay' not in js_text


def test_card_examples_are_served_by_backend_api():
    client = app.test_client()
    response = client.get('/api/card')

    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload.get('examples'), list)
    assert any(item.get('key') == 'rimaykullayki' for item in payload['examples'])
    assert any(item.get('key') == 'allinpunchay' for item in payload['examples'])


def test_main_ui_is_not_intentionally_hidden_and_uses_playful_status_labels():
    css_path = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'css' / 'style.css'
    js_path = Path(__file__).resolve().parents[1] / 'web' / 'static' / 'js' / 'app.js'
    css_text = css_path.read_text(encoding='utf-8')
    js_text = js_path.read_text(encoding='utf-8')

    assert '.topbar,\n.footer,\n.institution,' not in css_text
    assert '🎧' in js_text or '🤖' in js_text or '✨' in js_text


