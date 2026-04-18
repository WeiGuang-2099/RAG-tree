from app.services.parser_service import get_parser, parse_file, PARSER_REGISTRY
from app.parsers.python_parser import PythonParser
from app.parsers.javascript_parser import JavaScriptParser
from app.parsers.vue_parser import VueParser


def test_parser_registry():
    assert "py" in PARSER_REGISTRY
    assert "js" in PARSER_REGISTRY
    assert "ts" in PARSER_REGISTRY
    assert "tsx" in PARSER_REGISTRY
    assert "jsx" in PARSER_REGISTRY
    assert "vue" in PARSER_REGISTRY


def test_get_parser_python():
    parser = get_parser("py")
    assert isinstance(parser, PythonParser)


def test_get_parser_javascript():
    parser = get_parser("js")
    assert isinstance(parser, JavaScriptParser)


def test_get_parser_typescript():
    parser = get_parser("ts")
    assert isinstance(parser, JavaScriptParser)


def test_get_parser_unsupported():
    try:
        get_parser("ruby")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "ruby" in str(e)


def test_parse_file_python():
    result = parse_file("main.py", "def hello(): pass", "py")
    assert result["file_path"] == "main.py"
    assert result["language"] == "py"
    assert "nodes" in result
    assert "edges" in result


def test_parse_file_javascript():
    result = parse_file("app.js", "function greet() {}", "js")
    assert result["file_path"] == "app.js"
    assert "nodes" in result


def test_get_parser_vue():
    parser = get_parser("vue")
    assert isinstance(parser, VueParser)


def test_parse_file_vue():
    vue_code = "<template><div>{{ msg }}</div></template><script setup>const msg = 'hello'</script>"
    result = parse_file("App.vue", vue_code, "vue")
    assert result["file_path"] == "App.vue"
    assert result["language"] == "vue"
    assert "nodes" in result
    assert "edges" in result
