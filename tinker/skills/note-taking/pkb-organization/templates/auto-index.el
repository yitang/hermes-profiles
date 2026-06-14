;;; auto-index.el — Generate dynamic org-roam index cards
;;; 
;;; Usage: Put this code in your Emacs config (or eval it), then create an
;;; index file like `notes/index-git.org` with a heading that calls the function.
;;;
;;; Grouping strategy: filename keyword extraction + tag override fallback.

(defun pkb-index-for-topic (topic-keyword &optional limit max-age-days)
  "Generate an org-mode list of recently-modified notes matching TOPIC-KEYWORD.

Scans all files under `org-roam-directory', extracts topic from filename
(e.g., 'bash_source.org' -> 'bash'), cross-references with tags inside
the note body (:git: tag overrides filename grouping). Returns org-links
sorted by last modification time, descending.

Optional LIMIT (default 15) caps results. Optional MAX-AGE-DAYS limits
to notes modified within that many days — set to nil for no limit."
  (let* ((limit (or limit 15))
         (max-age (if max-age-days (* max-age-days 86400) nil))
         (roam-dir (or (bound-and-true-p org-roam-directory)
                       "~/matrix/tools/meta-tools/notes"))
         (all-notes (directory-files roam-dir t "\\.org$"))
         tag-pattern results notes-matched)

    ;; First pass: collect all matching notes with metadata
    (dolist (f (reverse all-notes))
      (when-let* ((base (file-name-sans-extension (file-name-nondirectory f)))
                  ;; Extract keyword from filename (after date prefix)
                  (fname-keyword (replace-regexp-in-string "^\\d+" "" base))
                  (fname-match (string-match-p fname-keyword topic))
                  tags-match note-content)
        (when-let ((content (with-temp-buffer
                             (insert-file-contents f)
                             (buffer-string))))
          ;; Check tag override
          (setq tag-pattern "#+TAGS:\\s-*:[^:]*\\b" topic "\\b[^:]*:")
          (setq tags-match (string-match-p tag-pattern content))
          (setq notes-matched (or fname-match tags-match))

          (when notes-matched
            (push `(,f ,(nth 5 (file-attributes f))
                       ,fname-keyword) results)))))

    ;; Sort by modification time descending
    (setq results (sort results (lambda (a b) (> (cadr a) (cadr b)))))

    ;; Trim to limit
    (setq results (seq-take results limit))

    ;; Format as org links
    (dolist (entry results)
      (let ((file (car entry))
            (modtime (cadr entry))
            (kw (caddr entry)))
        (org-link-add-text (format "* [[id:%s][%s]]" 
                                   (org-id-get-create file) kw))
        (insert "  "))

    results))
