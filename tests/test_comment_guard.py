import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
import comment_guard  # noqa: E402


def comments(name, src):
    return [t for _, t in comment_guard.split(name, src)[1]]


def same_code(name, a, b):
    return comment_guard.fingerprint(name, a) == comment_guard.fingerprint(name, b)


class Lexing(unittest.TestCase):
    def test_comment_markers_inside_strings_are_code(self):
        src = 'const u = "http://x"; const t = `a // b ${c}`; // real\n'
        self.assertEqual(comments("a.ts", src), ["// real"])

    def test_block_and_doc_comments(self):
        src = "/** Doc. */\nint x = 1; /* inline */\n/// dart doc\n"
        self.assertEqual(comments("a.dart", src), ["/** Doc. */", "/* inline */", "/// dart doc"])

    def test_dart_and_java_triple_quotes(self):
        self.assertEqual(comments("a.dart", "var s = '''\n// not\n''';\n"), [])
        self.assertEqual(comments("A.java", 'String s = """\n// not\n""";\n'), [])

    def test_rust_lifetimes_are_not_strings(self):
        self.assertEqual(comments("a.rs", "fn f<'a>(x: &'a str) {} // c\n"), ["// c"])

    def test_python_comments_and_docstrings(self):
        src = 'def f():\n    """Doc."""\n    x = "#no"  # yes\n    return x\n'
        self.assertEqual(comments("a.py", src), ['"""Doc."""', "# yes"])

    def test_shell_hash_inside_words(self):
        self.assertEqual(comments("a.sh", 'echo $# ${#x} a#b  # c\n'), ["# c"])

    def test_unsupported_type(self):
        with self.assertRaises(ValueError):
            comment_guard.split("a.unknownext", "")

    def test_css_has_no_line_comments(self):
        self.assertEqual(comments("a.css", "a { background: url(http://x/y.png); } /* c */\n"),
                         ["/* c */"])


PHP = """<p>// html, not a comment</p>
<?php
# hash
#[Attribute]
class A {
    public $u = "http://x"; // trailing
    public $m = 'one
// still the string';
    function f() {
        $s = <<<EOT
        // inside a heredoc
        EOT;
        $t = <<<'NOW'
        # inside a nowdoc
        NOW;
        return $s; // ends here ?> <b>// html again</b> <?php
    }
}
"""


class Php(unittest.TestCase):
    def test_comments(self):
        self.assertEqual(comments("a.php", PHP), ["# hash", "// trailing", "// ends here "])

    def test_editing_comments_keeps_code(self):
        edited = PHP.replace("# hash\n", "").replace(" // trailing", "")
        self.assertTrue(same_code("a.php", PHP, edited))

    def test_code_that_looks_like_comments_counts(self):
        for old, new in [("// inside a heredoc", "// CHANGED"), ("# inside a nowdoc", "# CHANGED"),
                         ("// still the string", "// CHANGED"), ("// html again", "// CHANGED"),
                         ("// html, not", "// CHANGED,"), ("#[Attribute]\n", "")]:
            self.assertFalse(same_code("a.php", PHP, PHP.replace(old, new)), old)


class Unchecked(unittest.TestCase):
    def test_modelled_files_are_checked(self):
        for name, src in [("a.ts", "const r = a / b / c; // ok\n"), ("a.rs", "fn f<'a>() {}\n"),
                          ("a.php", PHP), ("a.py", "x = 1\n"), ("a.yml", "a: b # c\n")]:
            self.assertIsNone(comment_guard.unchecked_reason(name, src), name)

    def test_unmodelled_syntax_is_reported(self):
        for name, src in [("a.ts", "const r = /\\/\\//g;\n"),
                          ("a.ts", "const t = `${`inner`}`;\n"),
                          ("a.rs", 'let s = r#"// x"#;\n'),
                          ("a.rs", "/* outer /* inner */ still */\n"),
                          ("a.cs", 'var s = @"C:\\dir\\";\n'),
                          ("a.swift", 'let s = #"\\(x)"#\n'),
                          ("a.dart", "var s = r'\\';\n"),
                          ("a.cpp", 'auto s = R"(// x)";\n'),
                          ("a.rb", "s = <<~EOS\n  # x\nEOS\n"),
                          ("a.sh", "cat <<EOF\n# x\nEOF\n"),
                          ("a.yml", "run: |\n  echo # x\n"),
                          ("a.py", "def f(:\n"),
                          ("a.unknownext", "")]:
            self.assertIsNotNone(comment_guard.unchecked_reason(name, src), (name, src))


class Fingerprint(unittest.TestCase):
    def test_comment_edits_do_not_count(self):
        a = "// old\nint x = 1; // trailing\n/* block */\n"
        b = "// new and longer\nint x = 1;\n"
        self.assertTrue(same_code("A.java", a, b))

    def test_code_edits_count(self):
        self.assertFalse(same_code("A.java", "int x = 1;\n", "int x = 2;\n"))
        self.assertFalse(same_code("a.ts", 's = "// a";\n', 's = "// b";\n'))

    def test_python_docstring_edit_does_not_count(self):
        a = 'def f():\n    """Old."""\n    return 1\n'
        b = 'def f():\n    """New."""\n    return 1\n'
        self.assertTrue(same_code("a.py", a, b))


class Cli(unittest.TestCase):
    def test_compare(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = pathlib.Path(d, "a.ts"), pathlib.Path(d, "b.ts")
            a.write_text("let x = 1; // c\n")
            b.write_text("let x = 1;\n")
            self.assertEqual(comment_guard.main(["compare", str(a), str(b)]), 0)
            b.write_text("let x = 2;\n")
            self.assertEqual(comment_guard.main(["compare", str(a), str(b)]), 1)
            b.write_text("let r = /\\/\\//;\n")
            self.assertEqual(comment_guard.main(["compare", str(a), str(b)]), 2)


if __name__ == "__main__":
    unittest.main()
