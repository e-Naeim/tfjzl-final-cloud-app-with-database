# Online Course Assessment (Django)

Based on IBM Skills Network's `tfjzl-final-cloud-app-with-database` starter.
Adds course questions, multiple-select choices, enrollment submissions, admin
inlines, exam forms, automatic scoring, detailed results and retakes.

## Run the disposable course demo

Python 3.10 or newer is supported. Run from this repository directory:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-lock.txt
export DJANGO_DEBUG=1
python manage.py migrate
python manage.py seed_demo
python manage.py changepassword admin
python manage.py runserver
```

If your lab lacks `venv`, run `pip install virtualenv` and
`virtualenv .venv` instead. Open `/onlinecourse/` for the app and `/admin/`
for course administration. `seed_demo` creates a synthetic admin with an
unusable password; choose its initial demo password interactively.
In the IBM lab, set `DJANGO_ALLOWED_HOSTS=.cognitiveclass.ai,localhost,127.0.0.1`
and use `runserver 0.0.0.0:8000`, then launch port 8000 through the lab UI.
The debug demo is not intended for production or real learner data.

## Verify

```sh
DJANGO_DEBUG=1 python manage.py test -v 2
DJANGO_DEBUG=1 python manage.py makemigrations --check --dry-run
DJANGO_SECRET_KEY='<your private deployment secret>' python manage.py check --deploy
```

Twenty tests cover exact multiple-selection scoring; wrong, incomplete and empty
answers; duplicate selections; malformed and cross-course choice IDs;
login/enrollment/ownership boundaries; retakes; admin registration; form rendering;
registration validation; and repeated enrollment. Passing uses the starter's
strict score threshold of greater than 80 percent. Selecting every choice does
not improperly award full credit.

## Security and deployment

Debug is off by default. Production requires a private `DJANGO_SECRET_KEY` and
an explicit allowed host list. Production enables HTTPS redirects, secure cookies,
and HSTS. Configure TLS, production static/media serving and a proper WSGI server
before public deployment; the development server is for the disposable course lab.
Never commit secrets, databases, sessions, or real user records.

## Submission

The screenshot-only peer option expects seven genuine captures: models, admin
source, admin site, course-detail source, submit/result views, URL routes, and
successful mock exam. This project also includes test coverage beyond that rubric.
Review and understand the implementation and the course's AI/Honor Code rules
before personally accepting the declaration or submitting.
