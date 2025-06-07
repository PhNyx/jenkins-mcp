import re

# Taken from SelfSupport.groovy and converted into Python file
# The idea is to scan the console log matching failure patterns, extract a reasonable amount of lines around each match, and limit to under 1 million tokens/
# 1 million tokens is about 750k characters so we also cap it around 1000 lines
def extract_error_block(log_text, max_lines=1000, keywords=None):
    """
    Extracts relevant error lines from a Jenkins log, surrounding each match with context.
    """
    if keywords is None:
        keywords = ["ERROR", "Exception", "Traceback", "FAILED", "Build failed", "Segmentation fault"]

    lines = log_text.splitlines()
    extracted = []
    added_indices = set()

    for i, line in enumerate(lines):
        if any(k.lower() in line.lower() for k in keywords):
            start = max(0, i - 10)
            end = min(len(lines), i + 20)
            for j in range(start, end):
                if j not in added_indices:
                    extracted.append(lines[j])
                    added_indices.add(j)

    # Trim to max_lines
    return "\n".join(extracted[-max_lines:])