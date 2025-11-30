import re

class CommentParser:
    """
    A tool to extract comments from code snippets for various programming languages
    using Regular Expressions.
    """

    def __init__(self):
        # ------------------------------------------------------------------
        # Regex Component Definitions
        # ------------------------------------------------------------------
        
        # Matches double quoted strings: "..."
        # Handles escaped quotes: \"
        self._double_quotes = r'"(?:\\.|[^"\\])*"'
        
        # Matches single quoted strings/chars: '...'
        self._single_quotes = r"'(?:\\.|[^'\\])*'"

        # Strict versions for Python to avoid consuming start of triple quotes
        # These lookahead to ensure a quote is NOT followed by another quote (preventing ' matching start of ''')
        self._double_quotes_strict = r'"(?!"")(?:\\.|[^"\\])*"'
        self._single_quotes_strict = r"'(?!'')(?:\\.|[^'\\])*'"
        
        # Matches backtick strings (JS template literals, Go raw strings): `...`
        self._backticks = r"`(?:\\.|[^`\\])*`"
        
        # Python Triple Quotes (Double and Single)
        self._py_triple_double = r'"""[\s\S]*?"""'
        self._py_triple_single = r"'''[\s\S]*?'''"

        # Comment Patterns
        self._slash_slash = r"//.*?$"       # // comment
        self._slash_star = r"/\*[\s\S]*?\*/" # /* block comment */
        self._hash = r"#.*?$"               # # comment

    def _get_pattern(self, language: str):
        """
        Constructs a specific compiled regex pattern for the given language.
        Returns a pattern with two groups: 
        Group 1: Content to skip (Strings/Literals)
        Group 2: Content to keep (Comments)
        """
        lang = language.lower()

        if lang == 'python':
            # Python:
            # Skip: "Standard" strings that are NOT triple quotes.
            # Keep: Hash comments (#) AND Triple Quotes (Docstrings/Block Comments).
            
            # Note: We use strict versions of single/double quotes in 'skippable' so they 
            # don't match the first quote of a triple-quote sequence.
            # e.g., ' matches the start of ''' if we aren't careful.
            skippable = f"{self._double_quotes_strict}|{self._single_quotes_strict}"
            keepable = f"{self._hash}|{self._py_triple_double}|{self._py_triple_single}"
            
        elif lang in ['c', 'c++', 'java', 'c#']:
            # C-Style:
            # Skip: Double quotes, Single quotes (chars)
            # Keep: // and /* ... */
            skippable = f"{self._double_quotes}|{self._single_quotes}"
            keepable = f"{self._slash_slash}|{self._slash_star}"
            
        elif lang in ['js', 'go', 'javascript']:
            # JS/Go:
            # Skip: Double quotes, Single quotes, Backticks
            # Keep: // and /* ... */
            skippable = f"{self._double_quotes}|{self._single_quotes}|{self._backticks}"
            keepable = f"{self._slash_slash}|{self._slash_star}"
            
        elif lang == 'php':
            # PHP:
            # Skip: Double quotes, Single quotes
            # Keep: //, #, and /* ... */
            skippable = f"{self._double_quotes}|{self._single_quotes}"
            keepable = f"{self._slash_slash}|{self._hash}|{self._slash_star}"
            
        else:
            raise ValueError(f"Unsupported language: {language}")

        # Combine into (SKIP)|(KEEP)
        # flags=re.MULTILINE | re.DOTALL is handled during compilation/search usually, 
        # but here we embed patterns that handle newlines (like [\s\S]).
        # We use re.MULTILINE for $ anchor matching.
        return re.compile(f"({skippable})|({keepable})", re.MULTILINE)

    def extract_comments(self, code: str, language: str) -> list[str]:
        """
        Parses the code and returns a list of comments.
        """
        pattern = self._get_pattern(language)
        comments = []

        # re.finditer is efficient for large strings
        for match in pattern.finditer(code):
            # group(1) is skippable (strings), group(2) is the comment
            if match.group(2):
                comments.append(match.group(2))
        
        return comments

# ------------------------------------------------------------------
# Usage Examples
# ------------------------------------------------------------------

if __name__ == "__main__":
    parser = CommentParser()

    # 1. Python Example
    py_code = """
    # This is a standard comment
    x = 10 
    s = "This string has a # inside it, which is NOT a comment"
    '''
    This is a multiline string, often used as a docstring.
    Now treated as a comment by the parser!
    '''
    y = 20 # Inline comment
    """
    print("--- Python Comments ---")
    print(parser.extract_comments(py_code, 'Python'))

    # 2. C++ / Java / C# Example
    cpp_code = """
    // Single line comment
    int main() {
        char* s = "http://url.com"; // Double slash inside string ignored
        /* Block comment 
           spanning lines
        */
        return 0;
    }
    """
    print("\n--- C++/Java Comments ---")
    print(parser.extract_comments(cpp_code, 'C++'))

    # 3. JavaScript Example (Template Literals)
    js_code = """
    // JS Comment
    const s = `This matches comments? // No, it's a string`;
    /* Block */
    """
    print("\n--- JS Comments ---")
    print(parser.extract_comments(js_code, 'JS'))

    # 4. PHP Example (Hash support)
    php_code = """
    <?php
    // C-style
    # Shell-style
    $url = "http://example.com"; 
    /* Block */
    """
    print("\n--- PHP Comments ---")
    print(parser.extract_comments(php_code, 'PHP'))