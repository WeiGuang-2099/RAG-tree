from app.parsers.python_parser import PythonParser
from app.parsers.javascript_parser import JavaScriptParser
from app.parsers.go_parser import GoParser
from app.parsers.java_parser import JavaParser
from app.parsers.vue_parser import VueParser


PYTHON_CODE = '''
import os
from sys import path

class MyClass:
    def method(self):
        return helper()

def helper():
    pass
'''

JS_CODE = '''
import React from 'react';

class App extends React.Component {
    render() {
        return <div>Hello</div>;
    }
}

function greet(name) {
    return "Hello " + name;
}
'''

GO_CODE = '''
package main

import (
    "fmt"
)

func main() {
    fmt.Println("Hello")
}

type Server struct {
    Port int
}
'''

JAVA_CODE = '''
import java.util.List;

public class Main extends Base {
    public static void main(String[] args) {
        System.out.println("Hello");
    }

    private void process() {}
}
'''

VUE_SETUP_CODE = '''
<template>
  <div>
    <MyButton @click="handleClick" />
  </div>
</template>

<script setup>
import { ref } from "vue"
import MyButton from "./MyButton.vue"

const count = ref(0)

function handleClick() {
  count.value++
}

const props = defineProps({
  title: String,
  items: Array
})

const emit = defineEmits(["update"])
</script>
'''

VUE_OPTIONS_CODE = '''
<template>
  <div><HeaderComponent /></div>
</template>

<script>
import HeaderComponent from "./HeaderComponent.vue"

export default {
  name: "AppLayout",
  components: { HeaderComponent },
  props: ["title"],
  emits: ["change"],
  methods: {
    handleSubmit() {}
  },
}
</script>
'''


def test_python_parser():
    parser = PythonParser()
    result = parser.parse(PYTHON_CODE)
    assert "nodes" in result
    assert "edges" in result
    node_names = [n["name"] for n in result["nodes"]]
    assert "MyClass" in node_names
    assert "helper" in node_names


def test_javascript_parser():
    parser = JavaScriptParser()
    result = parser.parse(JS_CODE)
    assert "nodes" in result
    node_names = [n["name"] for n in result["nodes"]]
    assert "App" in node_names
    assert "greet" in node_names


def test_go_parser():
    parser = GoParser()
    result = parser.parse(GO_CODE)
    assert "nodes" in result
    node_names = [n["name"] for n in result["nodes"]]
    assert "main" in node_names


def test_java_parser():
    parser = JavaParser()
    result = parser.parse(JAVA_CODE)
    assert "nodes" in result
    node_names = [n["name"] for n in result["nodes"]]
    assert "Main" in node_names


def test_vue_parser_setup():
    parser = VueParser()
    result = parser.parse(VUE_SETUP_CODE)
    assert "nodes" in result
    assert "edges" in result
    node_names = [n["name"] for n in result["nodes"]]
    assert "handleClick" in node_names
    assert "title" in node_names
    assert "items" in node_names
    edge_pairs = [(e["source"], e["target"]) for e in result["edges"]]
    assert ("AnonymousComponent", "handleClick") in edge_pairs


def test_vue_parser_options():
    parser = VueParser()
    result = parser.parse(VUE_OPTIONS_CODE)
    assert "nodes" in result
    node_names = [n["name"] for n in result["nodes"]]
    assert "AppLayout" in node_names
    assert "handleSubmit" in node_names
    assert "HeaderComponent" in node_names
