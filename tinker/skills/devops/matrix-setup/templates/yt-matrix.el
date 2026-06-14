;;; yt-matrix.el --- Simplified matrix setup for meta-* repos only  -*- lexical-binding: t; -*-

;; Replace the old pipeline: main.org → Python → transient_python.el
;; One clean alist, one macro — no codegen, no build step.
;;
;; Usage:
;;   (load "~/para/1_projects/org-roam-anywhere/yt-matrix.el")
;;   (yt/meta-enable)
;;
;; Then C-c m to launch the domain menu.

;;; Code:

(require 'cl-lib)

;; ─── The data: meta-* projects only ──────────────────────────────────────────

(defvar yt/meta-projects
  ;; Each entry: (domain-key domain-label
  ;;              (project-key project-label project-dir meta-dir) ...)
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
     ("tm" "Tools Meta"   "~/matrix/tools/meta-tools"       "~/matrix/tools/meta-tools")))
  "Alist of active matrix domains and their meta-* projects.
Each project: (key label project-dir meta-dir)")

(defvar yt/reflect-projects
  '(("rd" "Diaries"         "~/matrix/reflect/diaries")
    ("rm" "Reflect Meta"    "~/matrix/reflect/meta")
    ("rp" "Personal Finance" "~/matrix/reflect/personal_finance")
    ("rr" "Review"          "~/matrix/reflect/review"))
  "Reflect projects — no meta-* dir, no org-roam vault.")

;; ─── Capture template generator ─────────────────────────────────────────────

(defun yt/meta--capture-templates ()
  "Generate org-capture templates for all meta-* projects."
  (let (templates)
    (dolist (domain yt/meta-projects)
      (let ((domain-key (nth 0 domain))
            (domain-name (nth 1 domain))
            (projects (nthcdr 2 domain)))
        (push `(,(concat " " domain-key) ,domain-name) templates)
        (dolist (proj projects)
          (let ((key (nth 0 proj))
                (desc (nth 1 proj))
                (dir  (nth 2 proj))
                (meta (nth 3 proj)))
            (push `(,(concat key "t") ,(concat desc " TODO")
                    entry (file+headline ,(expand-file-name "main.org" dir) "TODOs")
                    "* TODO %?\n%U\n") templates)
            (push `(,(concat key "n") ,(concat desc " Note")
                    entry (file+headline ,(expand-file-name "main.org" dir) "Notes")
                    "* %?\n%U\n") templates)
            (push `(,(concat key "j") ,(concat desc " Journal")
                    entry
                    (file+function ,(expand-file-name "journal.org" dir)
                                   org-reverse-datetree-goto-read-date-in-file)
                    "* %<%H:%M> %?") templates)
            (push `(,(concat key "r") ,(concat desc " Roam")
                    plain "%?"
                    :target (file+head ,(expand-file-name
                                         (format-time-string "%Y%m%d_%H%M%S-${slug}.org")
                                         (expand-file-name "notes/" meta))
                                       "#+title: ${title}\n#+FILETAGS: :fleeting:\n")
                    :unnarrowed t) templates)))))
    (nreverse templates)))

;; ─── Agenda generator ───────────────────────────────────────────────────────

(defun yt/meta--agenda-commands ()
  "Generate org-agenda custom commands for all meta-* and reflect projects."
  (let (commands)
    (dolist (proj (append
                   (cl-loop for domain in yt/meta-projects
                            append (nthcdr 2 domain))
                   (cl-loop for p in yt/reflect-projects
                            collect (list (nth 0 p) (nth 1 p) (nth 2 p)))))
      (let ((key (nth 0 proj))
            (desc (nth 1 proj))
            (dir (nth 2 proj)))
        (push `(,key ,desc
                ((agenda "" ((org-agenda-overriding-header ,desc)))
                 (todo "NEXT")
                 (todo "TODO")
                 (todo "DONE"))
                ((org-agenda-files (directory-files-recursively ,dir ".*\\.org$"))))
              commands)))
    (nreverse commands)))

;; ─── Interactive dispatch ──────────────────────────────────────────────────

(defun yt/matrix3 ()
  "Meta-* projects quick access menu."
  (interactive)
  (let* ((domain-choice (read-multiple-choice
                          "Matrix domain: "
                          (cl-loop for d in yt/meta-projects
                                   collect (list (string-to-char (nth 0 d))
                                                 (nth 1 d)))))
         (domain (assoc (char-to-string (car domain-choice))
                        yt/meta-projects)))
    (when domain
      (yt/meta--project-action
       (car (nthcdr 2 domain))))))

(defun yt/meta--project-action (proj)
  "Choose an action for PROJ (the alist entry)."
  (let* ((key (nth 0 proj))
         (desc (nth 1 proj))
         (dir (nth 2 proj))
         (meta (nth 3 proj))
         (action (read-multiple-choice
                  (format "%s: " desc)
                  '((?t "TODO") (?n "Note") (?j "Journal") (?r "Roam")
                    (?d "Dired") (?a "Agenda")))))
    (pcase (car action)
      (?t (org-capture nil (concat key "t")))
      (?n (org-capture nil (concat key "n")))
      (?j (org-capture nil (concat key "j")))
      (?r (org-capture nil (concat key "r")))
      (?d (dired (expand-file-name dir)))
      (?a (org-agenda nil key)))))

;; ─── Activation ─────────────────────────────────────────────────────────────

;;;###autoload
(defun yt/meta-enable ()
  "Enable simplified matrix setup: capture templates, agenda, keybinding."
  (interactive)
  ;; Capture templates (prepend to existing)
  (setq org-capture-templates
        (append (yt/meta--capture-templates) org-capture-templates))
  ;; Agenda commands (prepend to existing)
  (setq org-agenda-custom-commands
        (append (yt/meta--agenda-commands) org-agenda-custom-commands))
  ;; Keybinding
  (global-set-key (kbd "C-c m") 'yt/matrix3))

(provide 'yt-matrix)
;;; yt-matrix.el ends here
