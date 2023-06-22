test:
	python spy.py --help
	python spy.py -p "Amstrad CPC" -g "253"
	python spy.py -p "Amstrad CPC" -g "253"
	python spy.py -p "Amstrad CPC" "Commodore 64" -g 10743 253
	python spy.py -p "Amstrad CPC" "Commodore 64" -g 10743 253

quality:
	pylama spy.py