PY ?= python3
SRC := src
VENV := .venv
APP := microscope-app

.PHONY: help run deb install uninstall dev clean

help:
	@echo "Target disponibili / Available targets:"
	@echo "  make deb        Costruisce il pacchetto .deb in dist/ / Build the .deb package into dist/"
	@echo "  make install    Installa il pacchetto .deb (sudo) / Install the .deb package (sudo)"
	@echo "  make uninstall  Disinstalla microscope-app (sudo) / Uninstall microscope-app (sudo)"
	@echo "  make run        Avvia l'app dal sorgente / Run the app from source"
	@echo "  make dev        Crea un virtualenv per lo sviluppo / Create a development virtualenv"
	@echo "  make clean      Rimuove gli artefatti di build / Remove build artifacts"

run:
	PYTHONPATH=$(SRC) $(PY) -m microscope_app

deb:
	./build-deb.sh

install: deb
	sudo apt-get install -y ./dist/$(APP)_*.deb

uninstall:
	sudo apt-get remove -y $(APP)

dev:
	$(PY) -m venv --system-site-packages $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements-dev.txt

clean:
	rm -rf build dist
	find $(SRC) -type d -name '__pycache__' -prune -exec rm -rf {} +
	rm -rf *.spec
