from quickstats import theme


def test_palette_falls_back_for_unknown_preferences() -> None:
    theme.configure("not-a-theme", "not-an-accent")
    palette = theme.current_palette()
    assert palette["background"] == theme.THEMES["graphite"]["background"]
    assert palette["accent"] == theme.ACCENTS["blue"]


def test_each_theme_exposes_complete_semantic_tokens() -> None:
    required = {"background", "surface", "surface_alt", "border", "text", "muted", "grid"}
    for name in theme.THEMES:
        theme.configure(name, "teal")
        palette = theme.current_palette()
        assert required <= palette.keys()
        assert palette["accent"] == theme.ACCENTS["teal"]


def test_stylesheet_uses_selected_theme_and_accent() -> None:
    stylesheet = theme.build_stylesheet("light", "rose")
    assert theme.THEMES["light"]["background"] in stylesheet
    assert theme.ACCENTS["rose"] in stylesheet



def test_custom_hex_accent_is_supported_and_invalid_values_fall_back() -> None:
    stylesheet = theme.build_stylesheet("graphite", "#12abef")
    assert "#12abef" in stylesheet
    theme.configure("graphite", "not-a-colour")
    assert theme.current_palette()["accent"] == theme.ACCENTS["blue"]
