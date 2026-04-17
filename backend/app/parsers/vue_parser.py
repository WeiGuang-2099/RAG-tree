"""Vue Single File Component (SFC) parser using regex-based approach.

Parses .vue files by extracting <template>, <script>, and <style> blocks,
then analyzes the script section for imports, components, data, methods,
computed properties, and lifecycle hooks.
"""

import re
from typing import Any

from app.parsers.base import BaseParser


class VueParser(BaseParser):
    """Parse Vue Single File Component source code into graph nodes and edges."""

    SCRIPT_BLOCK_PATTERN = re.compile(
        r"<script[^>]*>(.*?)</script>",
        re.MULTILINE | re.DOTALL,
    )
    TEMPLATE_BLOCK_PATTERN = re.compile(
        r"<template[^>]*>(.*?)</template>",
        re.MULTILINE | re.DOTALL,
    )
    STYLE_BLOCK_PATTERN = re.compile(
        r"<style[^>]*>(.*?)</style>",
        re.MULTILINE | re.DOTALL,
    )
    SCRIPT_SETUP_ATTR_PATTERN = re.compile(r'setup', re.IGNORECASE)
    COMPONENT_NAME_PATTERN = re.compile(
        r"(?:name\s*:\s*['\"](\w+)['\"])",
        re.MULTILINE,
    )
    IMPORT_PATTERN = re.compile(
        r"import\s+(?:\{[^}]*\}|\*\s+as\s+\w+|\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        re.MULTILINE,
    )
    COMPONENTS_OPTION_PATTERN = re.compile(
        r"components\s*:\s*\{([^}]*)\}",
        re.MULTILINE,
    )
    COMPONENT_REGISTRATION_PATTERN = re.compile(
        r"app\.component\s*\(\s*['\"](\w+)['\"]",
        re.MULTILINE,
    )
    METHOD_PATTERN = re.compile(
        r"(?:methods\s*:\s*\{)?\s*(?:async\s+)?(\w+)\s*\(\s*(?:\w+(?:\s*,\s*\w+)*)?\s*\)\s*\{",
        re.MULTILINE,
    )
    COMPUTED_PATTERN = re.compile(
        r"computed\s*:\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
        re.MULTILINE | re.DOTALL,
    )
    COMPUTED_NAME_PATTERN = re.compile(
        r"(\w+)\s*(?:\(\)|\{)",
        re.MULTILINE,
    )
    DATA_PATTERN = re.compile(
        r"data\s*\(\s*\)\s*\{",
        re.MULTILINE,
    )
    EMITS_PATTERN = re.compile(
        r"emits\s*:\s*\[([^\]]*)\]",
        re.MULTILINE,
    )
    DEFINE_EMITS_PATTERN = re.compile(
        r"defineEmits\s*<[^>]*>\s*\(\s*\[([^\]]*)\]",
        re.MULTILINE | re.DOTALL,
    )
    DEFINE_PROPS_PATTERN = re.compile(
        r"defineProps\s*(?:<[^>]*>|\(\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}\s*\))",
        re.MULTILINE | re.DOTALL,
    )
    LIFECYCLE_PATTERN = re.compile(
        r"(?:onMounted|onCreated|onUnmounted|onBeforeMount|onBeforeUnmount|"
        r"onUpdated|onBeforeUpdate|mounted|created|unmounted|beforeMount|"
        r"beforeUnmount|beforeCreate|updated|beforeUpdate|destroyed)\s*\(",
        re.MULTILINE,
    )
    TEMPLATE_TAG_PATTERN = re.compile(
        r"<(\w[\w-]*)",
        re.MULTILINE,
    )
    NATIVE_HTML_TAGS = frozenset({
        'div', 'span', 'p', 'a', 'img', 'ul', 'ol', 'li', 'h1', 'h2', 'h3',
        'h4', 'h5', 'h6', 'table', 'tr', 'td', 'th', 'thead', 'tbody', 'form',
        'input', 'button', 'select', 'option', 'textarea', 'label', 'section',
        'header', 'footer', 'nav', 'main', 'aside', 'article', 'template',
        'slot', 'component', 'transition', 'transition-group', 'keep-alive',
        'teleport', 'suspense', 'br', 'hr', 'strong', 'em', 'b', 'i', 'pre',
        'code', 'blockquote', 'iframe', 'video', 'audio', 'source', 'canvas',
        'svg', 'path', 'circle', 'rect', 'g', 'defs', 'linearGradient',
        'stop', 'text', 'tspan', 'clipPath', 'mask', 'pattern', 'use',
    })
    FUNC_DECL_PATTERN = re.compile(
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
        re.MULTILINE,
    )
    ARROW_FUNC_PATTERN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\(|[\w]+)\s*=>",
        re.MULTILINE,
    )

    def parse(self, source_code: str) -> dict[str, Any]:
        nodes = []
        edges = []

        script_match = self.SCRIPT_BLOCK_PATTERN.search(source_code)
        template_match = self.TEMPLATE_BLOCK_PATTERN.search(source_code)
        script_content = script_match.group(1).strip() if script_match else ""
        template_content = template_match.group(1).strip() if template_match else ""
        is_setup = bool(script_match and self.SCRIPT_SETUP_ATTR_PATTERN.search(script_match.group(0)))

        component_name = self._extract_component_name(source_code, script_content)

        script_start_line = self._get_line_number(source_code, script_match.group(0)) if script_match else 1

        nodes.append(
            self._make_node(
                name=component_name,
                node_type="Class",
                start_line=1,
                end_line=source_code.count("\n") + 1,
                source_code=f"<template>...</template><script>...</script>",
            )
        )

        imports = self.IMPORT_PATTERN.findall(script_content)
        for imp in imports:
            module_name = imp.split("/")[-1].split("\\")[-1]
            if module_name.startswith("."):
                module_name = imp.split("/")[-2] if "/" in imp else module_name
            nodes.append(
                self._make_node(
                    name=module_name,
                    node_type="Module",
                    start_line=self._get_line_number(source_code, imp),
                    end_line=self._get_line_number(source_code, imp),
                    source_code="",
                )
            )

        child_components = self._extract_child_components(
            script_content, template_content, is_setup
        )
        for comp_name in child_components:
            nodes.append(
                self._make_node(
                    name=comp_name,
                    node_type="Module",
                    start_line=0,
                    end_line=0,
                    source_code="",
                )
            )
            edges.append(
                self._make_edge(
                    source=component_name,
                    target=comp_name,
                    edge_type="imports",
                )
            )

        seen_names: set[str] = set()

        methods = self._extract_methods(script_content, is_setup)
        for method_name, method_line in methods:
            seen_names.add(method_name)
            actual_line = script_start_line + method_line
            nodes.append(
                self._make_node(
                    name=method_name,
                    node_type="Function",
                    start_line=actual_line,
                    end_line=actual_line,
                    source_code="",
                )
            )
            edges.append(
                self._make_edge(
                    source=component_name,
                    target=method_name,
                    edge_type="calls",
                )
            )

        computed = self._extract_computed(script_content)
        for computed_name in computed:
            seen_names.add(computed_name)
            nodes.append(
                self._make_node(
                    name=computed_name,
                    node_type="Function",
                    start_line=0,
                    end_line=0,
                    source_code="",
                )
            )
            edges.append(
                self._make_edge(
                    source=component_name,
                    target=computed_name,
                    edge_type="calls",
                )
            )

        props = self._extract_props(script_content, is_setup)
        for prop_name in props:
            nodes.append(
                self._make_node(
                    name=prop_name,
                    node_type="Function",
                    start_line=0,
                    end_line=0,
                    source_code="",
                )
            )

        emits = self._extract_emits(script_content, is_setup)
        for emit_name in emits:
            nodes.append(
                self._make_node(
                    name=f"emit:{emit_name}",
                    node_type="Function",
                    start_line=0,
                    end_line=0,
                    source_code="",
                )
            )

        for match in self.FUNC_DECL_PATTERN.finditer(script_content):
            func_name = match.group(1)
            if func_name in seen_names:
                continue
            if func_name in {"defineProps", "defineEmits", "defineExpose", "withDefaults"}:
                continue
            seen_names.add(func_name)
            nodes.append(
                self._make_node(
                    name=func_name,
                    node_type="Function",
                    start_line=script_start_line + script_content[:match.start()].count("\n"),
                    end_line=script_start_line + script_content[:match.start()].count("\n"),
                    source_code=match.group(0),
                )
            )

        for match in self.ARROW_FUNC_PATTERN.finditer(script_content):
            func_name = match.group(1)
            if func_name in seen_names:
                continue
            seen_names.add(func_name)
            nodes.append(
                self._make_node(
                    name=func_name,
                    node_type="Function",
                    start_line=script_start_line + script_content[:match.start()].count("\n"),
                    end_line=script_start_line + script_content[:match.start()].count("\n"),
                    source_code=match.group(0),
                )
            )

        return {"nodes": nodes, "edges": edges}

    def _extract_component_name(self, source_code: str, script_content: str) -> str:
        name_match = self.COMPONENT_NAME_PATTERN.search(script_content)
        if name_match:
            return name_match.group(1)
        filename_patterns = [
            re.compile(r"(\w+)\.vue$", re.IGNORECASE),
        ]
        for pattern in filename_patterns:
            match = pattern.search(source_code)
            if match:
                return match.group(1)
        return "AnonymousComponent"

    def _extract_child_components(
        self, script_content: str, template_content: str, is_setup: bool
    ) -> list[str]:
        components = set()

        if not is_setup:
            comp_match = self.COMPONENTS_OPTION_PATTERN.search(script_content)
            if comp_match:
                for name in re.findall(r"(\w+)", comp_match.group(1)):
                    components.add(name)

        for match in self.COMPONENT_REGISTRATION_PATTERN.finditer(script_content):
            components.add(match.group(1))

        if template_content:
            for match in self.TEMPLATE_TAG_PATTERN.finditer(template_content):
                tag = match.group(1)
                if "-" in tag or (tag[0].isupper() and tag not in self.NATIVE_HTML_TAGS):
                    components.add(tag)

        return sorted(components)

    def _extract_methods(self, script_content: str, is_setup: bool) -> list[tuple[str, int]]:
        methods = []
        seen = set()

        if is_setup:
            for match in self.FUNC_DECL_PATTERN.finditer(script_content):
                name = match.group(1)
                if name not in seen and name not in {"defineProps", "defineEmits", "defineExpose", "withDefaults"}:
                    seen.add(name)
                    line_num = script_content[:match.start()].count("\n")
                    methods.append((name, line_num))

            for match in self.ARROW_FUNC_PATTERN.finditer(script_content):
                name = match.group(1)
                if name not in seen:
                    seen.add(name)
                    line_num = script_content[:match.start()].count("\n")
                    methods.append((name, line_num))
        else:
            in_methods = False
            brace_depth = 0
            for line in script_content.split("\n"):
                stripped = line.strip()
                if re.match(r"methods\s*:\s*\{", stripped):
                    in_methods = True
                    brace_depth = stripped.count("{") - stripped.count("}")
                    continue
                if in_methods:
                    brace_depth += stripped.count("{") - stripped.count("}")
                    method_match = re.match(r"(?:async\s+)?(\w+)\s*\(", stripped)
                    if method_match and method_match.group(1) not in seen:
                        name = method_match.group(1)
                        seen.add(name)
                        methods.append((name, 0))
                    if brace_depth <= 0:
                        in_methods = False

        return methods

    def _extract_computed(self, script_content: str) -> list[str]:
        computed = []
        match = self.COMPUTED_PATTERN.search(script_content)
        if match:
            for name_match in self.COMPUTED_NAME_PATTERN.finditer(match.group(1)):
                name = name_match.group(1)
                if name not in {"get", "set"}:
                    computed.append(name)
        return computed

    PROPS_OBJECT_PATTERN = re.compile(
        r"props\s*:\s*\{",
        re.MULTILINE,
    )
    PROPS_ARRAY_PATTERN = re.compile(
        r"props\s*:\s*\[([^\]]*)\]",
        re.MULTILINE,
    )
    PROP_INNER_KEYS = frozenset({"type", "default", "required", "validator"})
    PROP_NAME_PATTERN = re.compile(
        r"^\s{2,8}(\w+)\s*:\s*(?:String|Number|Boolean|Array|Object|Function|Symbol\b|\{)",
        re.MULTILINE,
    )

    def _extract_props(self, script_content: str, is_setup: bool) -> list[str]:
        props = []
        seen = set()
        if is_setup:
            match = self.DEFINE_PROPS_PATTERN.search(script_content)
            if match and match.group(1):
                for name in self.PROP_NAME_PATTERN.findall(match.group(1)):
                    if name not in seen and name not in self.PROP_INNER_KEYS:
                        seen.add(name)
                        props.append(name)
        else:
            obj_match = self.PROPS_OBJECT_PATTERN.search(script_content)
            if obj_match:
                props_block = self._extract_balanced_block(script_content, obj_match.end() - 1)
                for name in self.PROP_NAME_PATTERN.findall(props_block):
                    if name not in seen and name not in self.PROP_INNER_KEYS:
                        seen.add(name)
                        props.append(name)
            arr_match = self.PROPS_ARRAY_PATTERN.search(script_content)
            if arr_match:
                for name in re.findall(r"['\"](\w+)['\"]", arr_match.group(1)):
                    if name not in seen:
                        seen.add(name)
                        props.append(name)
        return props

    def _extract_balanced_block(self, source: str, open_brace_pos: int) -> str:
        depth = 0
        start = open_brace_pos
        for i in range(open_brace_pos, len(source)):
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
                if depth == 0:
                    return source[start + 1 : i]
        return source[start + 1 :]

    def _extract_emits(self, script_content: str, is_setup: bool) -> list[str]:
        emits = []
        if is_setup:
            match = self.DEFINE_EMITS_PATTERN.search(script_content)
            if match:
                for name in re.findall(r"['\"](\w+)['\"]", match.group(1)):
                    emits.append(name)
        else:
            match = self.EMITS_PATTERN.search(script_content)
            if match:
                for name in re.findall(r"['\"](\w+)['\"]", match.group(1)):
                    emits.append(name)
        return emits

    def _get_line_number(self, source: str, substring: str) -> int:
        idx = source.find(substring)
        if idx == -1:
            return 0
        return source[:idx].count("\n") + 1
