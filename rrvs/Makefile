clean:
	find . -name \*.pyc -delete
	find . -name \*__pycache__ -delete
	find . -name \*log.txt -delete

rm_setup:
	rm -rf build dist

build_exec:
	pyinstaller --onefile rrvs/client.py