# Filename Keyword Extraction for Index Cards

When building auto-generated index cards from flat timestamped org notes, filenames are the primary topic classifier.

## Format of meta-tools notes

```
YYYYMMDDHHMMSS-topic_keyword_underscore_separated.org
```

Date prefix is always present and variable length (8 or 14 digits). After a hyphen, the topic keyword starts, followed by underscores and more description words.

## Extraction algorithm

1. Strip `.org` extension
2. Remove leading date prefix: `^[0-9]{8}[0-9]*-`
3. Take the first underscore-separated segment after the date
4. Lowercase it

### Examples

| Filename | After date strip | First segment | Keyword |
|----------|-----------------|---------------|---------|
| `20250820100958-bash_source` | `bash_source` | `bash` | `bash` |
| `20260505112647-hermes_agent` | `hermes_agent` | `hermes` | `hermes` |
| `20260219154238-llama_cpp` | `llama_cpp` | `llama` | `llama` |
| `20260520183926-git_worktree` | `git_worktree` | `git` | `git` |
| `20260602104339-per_directory_local_variables` | `per_directory_local_variables` | `per` | `per` (not a known topic) |

## Edge cases

- **No underscore after keyword**: If the filename after date stripping has no underscores (e.g., `20260511142203-ngrok.org`), the entire stem after the hyphen IS the keyword.
- **Non-standard filenames**: Some notes may not follow this pattern. They won't match any known topic and will be excluded from index cards by default (or could appear in a catch-all "other" section).
- **Multiple matches**: If a note's keyword maps to multiple topics, use the first entry in the topic map ordering.

## Implementation notes (elish)

In `#+begin_src elish{}` blocks, the extraction function looks like:

```elish
(defun extract-keyword (filename)
  (let* ((name (replace-regexp-in-string "\\.org$" "" filename))
         (after-date (replace-regexp-in-string "^[0-9]\\{8\\}[0-9]*-" "" name))
         (seg (car (split-string after-date "_"))))
    (downcase seg)))
```

## When to fall back to tags

If the keyword from filename is ambiguous or wrong, check for `#+TAGS:` in the note body as a safety net. This hybrid approach works when:
- A note covers multiple topics (e.g., "hermes on ssh" — keyword says `hermes`, but tag might say `ssh`)
- The filename uses an unusual naming convention

Tag fallback only activates if no explicit topic mapping exists in the topic map for the extracted keyword.
