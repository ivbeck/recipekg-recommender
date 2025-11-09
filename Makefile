export FLASK_APP = backend.main
export FLASK_ENV = development
export EXPLAIN_TEMPLATE_LOADING = true

VENV = .venv
ACTIVATE = . $(VENV)/bin/activate

# make it work on windows too
ifeq ($(OS),Windows_NT)
    ACTIVATE = $(VENV)/Scripts/activate
endif

all: 
        $(ACTIVATE) && flask run
