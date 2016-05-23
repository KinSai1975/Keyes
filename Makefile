.PHONY: clean-pyc ext-test test tox-test test-with-mem upload-docs docs audit

all: clean-pyc test

test:
	py.test tests examples

tox-test:
	tox

audit:
	python setup.py audit

release:
	python scripts/make-release.py

ext-test:
	python tests/keyesext_test.py --browse

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

upload-docs:
	$(MAKE) -C docs html dirhtml latex epub
	$(MAKE) -C docs/_build/latex all-pdf
	cd docs/_build/; mv html keyes-docs; zip -r keyes-docs.zip keyes-docs; mv keyes-docs html
	rsync -a docs/_build/dirhtml/ flow.srv.pocoo.org:/srv/websites/keyes.pocoo.org/docs/
	rsync -a docs/_build/latex/keyes.pdf flow.srv.pocoo.org:/srv/websites/keyes.pocoo.org/docs/keyes-docs.pdf
	rsync -a docs/_build/keyes-docs.zip flow.srv.pocoo.org:/srv/websites/keyes.pocoo.org/docs/keyes-docs.zip
	rsync -a docs/_build/epub/keyes.epub flow.srv.pocoo.org:/srv/websites/keyes.pocoo.org/docs/keyes-docs.epub

# ebook-convert docs: http://manual.calibre-ebook.com/cli/ebook-convert.html
ebook:
	@echo 'Using .epub from `make upload-docs` to create .mobi.'
	@echo 'Command `ebook-covert` is provided by calibre package.'
	@echo 'Requires X-forwarding for Qt features used in conversion (ssh -X).'
	@echo 'Do not mind "Invalid value for ..." CSS errors if .mobi renders.'
	ssh -X pocoo.org ebook-convert /var/www/keyes.pocoo.org/docs/keyes-docs.epub /var/www/keyes.pocoo.org/docs/keyes-docs.mobi --cover http://keyes.pocoo.org/docs/_images/logo-full.png --authors 'Armin Ronacher'

docs:
	$(MAKE) -C docs html
