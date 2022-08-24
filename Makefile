VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
PYUIC = $(VENV)/bin/pyuic5
PYRCC = $(VENV)/bin/pyrcc5
PYINST = $(VENV)/bin/pyinstaller
NUITKA = $(VENV)/bin/nuitka

UI = src/package/ui/ui_main.py src/package/ui/ui_settings.py
RES = src/resources.qrc

# RUNING FROM PYTHON
run_cli: $(VENV)/bin/activate
	$(PYTHON) src/osmad_cli.py

run_gui: $(PYUIC) $(PYRCC) $(UI) res_file
	$(PYTHON) src/osmad_gui.py

%.py: %.ui
	$(PYUIC) -o $@ $<

res_file: $(RES)
	$(PYRCC) -o src/resources_rc.py $(RES)

# BINARY
build: build_cli build_gui
build_cli: $(VENV)/bin/activate $(PYINST)
	$(PYINST) osmad_cli.spec

build_gui: $(VENV)/bin/activate $(PYINST) $(PYUIC) $(PYRCC) $(UI) res_file
	$(PYINST) osmad_gui.spec

nuitka: alt_cli alt_gui
alt_cli: $(VENV)/bin/activate $(NUITKA)
	$(NUITKA) --output-dir=nuitka_build --follow-imports --onefile --lto=yes --windows-icon-from-ico=.\src\icons\base\app_icon.ico .\src\osmad_cli.py

alt_gui: $(VENV)/bin/activate $(NUITKA) $(PYUIC) $(PYRCC) $(UI) res_file
	$(NUITKA) --output-dir=nuitka_build --follow-imports --onefile --lto=yes --enable-plugin=pyqt5 --windows-disable-console --windows-icon-from-ico=.\src\icons\base\app_icon.ico .\src\osmad_gui.py

# VENV RELATED
$(VENV)/bin/activate: requirements_cli.txt
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -r requirements_cli.txt

$(PYRCC): $(PYUIC)
$(PYUIC):
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -r requirements_gui.txt

$(PYINST):
	$(PYTHON) -m venv $(VENV)
	$(PIP) install pyinstaller

$(NUITKA):
	$(PYTHON) -m venv $(VENV)
	$(PIP) install nuitka zstandard ordered-set

# CLEANING STUFF
mrproper: clean
	@rm -fr build
	@rm -fr dist
	@rm -fr out
	@rm -fr assets
	@rm -fr nuitka_build
	@rm -fr ~/.osm-ad

clean_res:
	@find . -type f -wholename '*/ui/ui_*.py' -delete
	@find . -type f -name 'resource_rc.py' -delete

clean: clean_res
	@find . -type f -name '*.pyc' -delete
	@find . -type d -name '__pycache__' -delete
	@rm -rf $(VENV)
