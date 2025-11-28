import random

from magika import Magika

from collections import Counter


PLID_FEATURES = {
    "Python": {
        "Keyword": {
            "def", "elif", "if", "else", "import", "from", "as", "try", "except", 
            "finally", "raise", "with", "assert", "lambda", "class", "pass", 
            "yield", "global", "nonlocal", "del", "async", "await", "None", 
            "True", "False", "and", "or", "not", "is", "in"
        },
        "Operator": {
            "->",  # Type hints
            "**",  # Power
            "//",  # Floor division
            ":=",  # Walrus operator
            "@"    # Decorator
        }
    },
    "C++": {
        "Keyword": {
            "template", "typename", "class", "struct", "union", "virtual", 
            "override", "final", "public:", "private:", "protected:", "friend", 
            "using", "namespace", "inline", "constexpr", "consteval", "nullptr", 
            "this", "new", "delete", "operator", "try", "catch", "throw", 
            "include", "std" # technically std is a namespace, but high signal
        },
        "Operator": {
            "::",  # Scope resolution
            "->",  # Pointer member access
            "<<", ">>", # Stream operators
            "&", "*"    # Address/Dereference (context dependent)
        }
    },
    "Java": {
        "Keyword": {
            "public", "private", "protected", "static", "final", "void", "class", 
            "interface", "extends", "implements", "abstract", "native", "synchronized", 
            "transient", "volatile", "throws", "package", "import", "new", "instanceof", 
            "super", "this", "null", "boolean", "byte", "char"
        },
        "Operator": {
            ">>>", # Unsigned right shift
            "::",  # Method reference (Java 8+)
            "@"    # Annotation indicator
        }
    },
    "Go": {
        "Keyword": {
            "func", "package", "import", "type", "struct", "interface", "map", 
            "chan", "go", "defer", "range", "select", "case", "fallthrough", 
            "var", "const", "nil"
        },
        "Operator": {
            ":=",  # Short declaration (Very high signal)
            "<-",  # Channel operator
            "...", # Variadic
            "&^"   # Bit clear
        }
    },
    "PHP": {
        "Keyword": {
            "function", "echo", "print", "array", "foreach", "as", "use", "namespace", 
            "global", "public", "private", "protected", "static", "final", "trait", 
            "clone", "include", "require", "isset", "empty", "die", "exit", 
            "null", "__construct"
        },
        "Operator": {
            "=>",  # Array key-value separator
            "->",  # Object operator
            "::",  # Scope resolution
            "===", "!==", # Strict comparison
            "<=>", # Spaceship operator
            "$"    # Variable prefix (Pygments often catches this as distinct)
        }
    },
    "C#": {
        "Keyword": {
            "namespace", "using", "class", "struct", "interface", "enum", "delegate", 
            "event", "public", "private", "internal", "protected", "static", "readonly", 
            "volatile", "virtual", "override", "sealed", "abstract", "async", "await", 
            "var", "get", "set", "value", "out", "ref", "in", "params", "base", "this", 
            "null", "true", "false", "checked", "unchecked", "fixed", "lock"
        },
        "Operator": {
            "??",  # Null coalescing
            "??=", # Null coalescing assignment
            "?.",  # Null conditional
            "=>"   # Lambda arrow
        }
    },
    "C": {
        "Keyword": {
            "int", "char", "float", "double", "void", "long", "short", "signed", 
            "unsigned", "struct", "union", "enum", "typedef", "sizeof", "static", 
            "extern", "auto", "register", "const", "volatile", "return", "if", 
            "else", "switch", "case", "default", "while", "do", "for", "break", 
            "continue", "goto", "include", "define"
        },
        "Operator": {
            "->",  # Struct pointer access
            ".",   # Struct member access
            "&",   # Address of
            "*"    # Pointer
        }
    },
    "JS": {
        "Keyword": {
            "function", "var", "let", "const", "if", "else", "switch", "for", 
            "while", "do", "break", "continue", "return", "try", "catch", "finally", 
            "throw", "new", "this", "delete", "typeof", "instanceof", "void", 
            "in", "of", "class", "extends", "super", "import", "export", "default", 
            "async", "await", "yield", "debugger", "undefined", "null", "NaN", 
            "true", "false", "console", "window", "document"
        },
        "Operator": {
            "===", "!==", # Strict equality
            "=>",         # Arrow function
            "...",        # Spread/Rest
            "`"           # Template literal backtick
        }
    }
}

MAGIKA2SEMEVAL = {
    "python": "Python",
    "cpp": "C++",
    "java": "Java",
    "go": "Go",
    "php": "PHP",
    "cs": "C#",
    "c": "C",
    "javascript": "JS",
}


class ProgrammingLanguageIdentifier:
    def __init__(self):
        self.features = PLID_FEATURES

    def identify(self, tokens):
        feature_counter = Counter({lang: 0 for lang in self.features.keys()})
        for lang, features in self.features.items():
            for text_base in tokens:
                text, base = text_base[0], text_base[1]
                if (text in features["Keyword"]) and (base == "Keyword"):
                    feature_counter[lang] += 1
                if (text in features["Operator"]) and (base == "Operator"):
                    feature_counter[lang] += 1
        print(feature_counter)
        return max(feature_counter, key=feature_counter.get)


class PlidWithMagika:
    def __init__(self):
        self.predictor = Magika()

    def identify(self, text, n_segments=5, overlap_ratio=0.5):
        # Sweep through text with overlapping segments
        segment_labels = []
        text_len = len(text)
        if n_segments <= 1 or text_len == 0:
            segment_labels = []
        else:
            segment_length = max(1, text_len // n_segments)
            step = max(1, int(segment_length * (1 - overlap_ratio)))
            indices = list(range(0, max(text_len - segment_length + 1, 1), step))
            # Guarantee we always cover the last region
            if (len(indices) < n_segments and text_len > segment_length) or (indices and (indices[-1] + segment_length < text_len)):
                indices.append(text_len - segment_length)
            for start in indices[:n_segments]:
                end = start + segment_length
                segment = text[start:end]
                segment_label = self.predictor.identify_bytes(segment.encode("utf-8")).output.label
                segment_labels.append(segment_label)
        segment_labels = Counter(segment_labels).most_common(10)
        segment_labels = [MAGIKA2SEMEVAL[label] for label, _ in segment_labels if label in list(MAGIKA2SEMEVAL.keys())]
        segment_label = segment_labels[0] if len(segment_labels) > 0 else random.choice(list(PLID_FEATURES.keys()))
        return segment_label