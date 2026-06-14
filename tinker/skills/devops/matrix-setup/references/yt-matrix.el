;;; yt-matrix.el --- Simplified matrix setup for meta-* repos only  -*- lexical-binding: t; -*-

;; A single-file replacement for the old main.org → Python → transient_python.el pipeline.
;; Fully data-driven — edit yt/meta-projects to add/remove domains.
;; Load with:  (load "~/para/1_projects/org-roam-anywhere/yt-matrix.el")
;; Activate:   (yt/meta-enable)
;; Then C-c m shows a transient popup for matrix domain selection.
;; Note: requires org-roam to be loaded (for org-roam-node-find, org-roam-directory).

(require 'cl-lib)

;; Forward declarations — org-roam loads later, but we let-bind these vars
(defvar org-roam-directory)
(defvar org-roam-db-location)

;; Forward declarations for variables defined by packages loaded later
(defvar org-roam-directory)
(defvar org-roam-db-location)

;; ─── The data — edit this to add/remove domains ────────────────────────────

(defvar yt/meta-projects
  '(("d" "Data Science"
     ("dm" "DS Meta"      "~/matrix/ds/meta-ds"            "~/matrix/ds/meta-ds"))
    ("f" "Finance"
     ("fm" "Finance Meta" "~/matrix/finance/meta-finance"   "~/matrix/finance/meta-finance"))
    ("h" "Health"
     ("hm" "Health Meta"  "~/matrix/health/meta-health"     "~/matrix/health/meta-health"))
    ("H" "Hobbies"
     ("Hm" "Hobbies Meta" "~/matrix/hobbies/meta-hobbies"   "~/matrix/hobbies/meta-hobbies"))
    ("l" "Learning"
     ("lm" "Learning Meta" "~/matrix/learning/meta-learning" "~/matrix/learning/meta-learning"))
    ("t" "Tools"
     ("tm" "Tools Meta"   "~/matrix/tools/meta-tools"       "~/matrix/tools/meta-tools"))))

(defvar yt/reflect-projects
  '(("rd" "Diaries"         "~/matrix/reflect/diaries")
    ("rm" "Reflect Meta"    "~/matrix/reflect/meta")
    ("rp" "Personal Finance" "~/matrix/reflect/personal_finance")
    ("rr" "Review"          "~/matrix/reflect/review")))

(defun yt/meta--capture-templates ()
  (let (templates)
    (push '("r" "Roam") templates)
    (dolist (domain yt/meta-projects)
      (let ((domain-key (nth 0 domain)) (domain-name (nth 1 domain))
            (projects (nthcdr 2 domain)))
        (push `(,(concat "r" domain-key) ,domain-name
                entry (function (lambda ()
                                 (yt/meta--roam-capture
                                  (nth 3 (car (nthcdr 2 (assoc ,domain-key yt/meta-projects)))))))
                "") templates)
        (push `(,(concat " " domain-key) ,domain-name) templates)
        (dolist (proj projects)
          (let ((key (nth 0 proj)) (desc (nth 1 proj)) (dir (nth 2 proj)))
            (push `(,(concat key "t") ,(concat desc " TODO")
                    entry (file+headline ,(expand-file-name "main.org" dir) "TODOs")
                    "* TODO %?\n%U\n") templates)
            (push `(,(concat key "n") ,(concat desc " Note")
                    entry (file+headline ,(expand-file-name "main.org" dir) "Notes")
                    "* %?\n%U\n") templates)
            (push `(,(concat key "j") ,(concat desc " Journal")
                    entry (file+function ,(expand-file-name "journal.org" dir)
                           org-reverse-datetree-goto-read-date-in-file)
                    "* %<%H:%M> %?") templates)))))
    (nreverse templates)))

(defun yt/meta--agenda-commands ()
  (let (commands)
    (dolist (proj (append (cl-loop for d in yt/meta-projects append (nthcdr 2 d))
                          (cl-loop for p in yt/reflect-projects
                                   collect (list (nth 0 p) (nth 1 p) (nth 2 p)))))
      (let ((key (nth 0 proj)) (desc (nth 1 proj)) (dir (nth 2 proj)))
        (push `(,key ,desc
                ((agenda "" ((org-agenda-overriding-header ,desc)))
                 (todo "NEXT") (todo "TODO") (todo "DONE"))
                ((org-agenda-files (directory-files-recursively ,dir ".*\\.org$"))))
              commands)))
    (nreverse commands)))

(defvar yt/meta--cur nil "Current project for the action transient.")

(defun yt/meta--roam-capture (meta-dir)
  "Open org-roam-node-find in META-DIR/notes/ and return the buffer."
  (interactive)
  (let ((org-roam-directory (expand-file-name "notes/" meta-dir))
        (org-roam-db-location (expand-file-name "org-roam.db"
                                (expand-file-name "notes/" meta-dir))))
    (org-roam-node-find))
  (current-buffer))

(defun yt/meta--select-by-key (key)
  "Select a matrix domain by KEY and show actions."
  (interactive)
  (let ((domain (assoc key yt/meta-projects)))
    (when domain
      (setq yt/meta--cur (car (nthcdr 2 domain)))
      (transient-setup 'yt/meta--action-transient))))

(defun yt/meta--action/todo () (interactive) (org-capture nil (concat (nth 0 yt/meta--cur) "t")))
(defun yt/meta--action/note () (interactive) (org-capture nil (concat (nth 0 yt/meta--cur) "n")))
(defun yt/meta--action/journal () (interactive) (org-capture nil (concat (nth 0 yt/meta--cur) "j")))
(defun yt/meta--action/roam () (interactive) (yt/meta--roam-capture (nth 3 yt/meta--cur)))
(defun yt/meta--action/dired () (interactive) (dired (expand-file-name (nth 2 yt/meta--cur))))
(defun yt/meta--action/agenda () (interactive) (org-agenda nil (nth 0 yt/meta--cur)))

(transient-define-prefix yt/meta--action-transient ()
  "Actions for the selected matrix project."
  ["Actions"
   [("t" "TODO"    yt/meta--action/todo)
    ("n" "Note"    yt/meta--action/note)
    ("j" "Journal" yt/meta--action/journal)
    ("r" "Roam"    yt/meta--action/roam)
    ("d" "Dired"   yt/meta--action/dired)
    ("a" "Agenda"  yt/meta--action/agenda)]])

;; Build main transient from data — avoids hardcoding domain entries
(eval
 `(transient-define-prefix yt/matrix3 ()
    "Matrix domains quick access."
    ["Matrix"
     ,(vconcat
       (cl-loop for d in yt/meta-projects
                collect
                `(,(nth 0 d) ,(nth 1 d)
                  (lambda () (interactive)
                    (yt/meta--select-by-key ,(nth 0 d))))))]
    ["Reflect"
     ,(vconcat
       (cl-loop for p in yt/reflect-projects
                collect
                `(,(nth 0 p) ,(nth 1 p)
                  (lambda () (interactive)
                    (dired ,(expand-file-name (nth 2 p)))))))]))

(defun yt/meta-enable ()
  (interactive)
  (setq org-capture-templates
        (append (yt/meta--capture-templates) org-capture-templates))
  (setq org-agenda-custom-commands
        (append (yt/meta--agenda-commands) org-agenda-custom-commands))
  (global-set-key (kbd "C-c m") 'yt/matrix3)
  (global-set-key (kbd "C-c r") 'yt/meta--roam-dispatch))

(defun yt/meta--roam-dispatch ()
  "Pick a domain and open org-roam-node-find in its vault."
  (interactive)
  (let* ((choices (cl-loop for d in yt/meta-projects
                           collect (list (string-to-char (nth 0 d)) (nth 1 d))))
         (choice (read-multiple-choice "Roam to domain: " choices))
         (domain (assoc (char-to-string (car choice)) yt/meta-projects))
         (proj (car (nthcdr 2 domain)))
         (meta-dir (nth 3 proj)))
    (let ((org-roam-directory (expand-file-name "notes/" meta-dir))
          (org-roam-db-location (expand-file-name "org-roam.db"
                                  (expand-file-name "notes/" meta-dir))))
      (org-roam-node-find))))

(provide 'yt-matrix)
