from app.modules.messaging.service import MessagingService


def test_template_render_replaces_known_tokens() -> None:
    source = "Hello {{name}}, due {{amount}}"
    rendered = MessagingService._render_template(source, {"name": "Pulak", "amount": "1200"})
    assert rendered == "Hello Pulak, due 1200"


def test_template_render_keeps_unknown_tokens() -> None:
    source = "Hello {{name}}, code {{code}}"
    rendered = MessagingService._render_template(source, {"name": "Pulak"})
    assert rendered == "Hello Pulak, code {{code}}"
