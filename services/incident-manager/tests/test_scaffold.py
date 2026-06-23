def test_brasaland_shared_importable() -> None:
    try:
        import brasaland_shared  # noqa: F401
    except ImportError as error:
        raise AssertionError(
            "brasaland_shared is not importable — run pip install -r requirements.txt "
            "from services/incident-manager/"
        ) from error
