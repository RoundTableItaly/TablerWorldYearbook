# TablerWorldYearbook

TablerWorldYearbook

## Install

    pipenv install

## Update

    pipenv update

## Run

    pipenv run python .\main.py

## Build exe

    pipenv run pyinstaller -F --windowed .\main.py

## Env

    Create a file named `.env` and add the following lines, taking care of modifying the values.

```
    API_BASE_URL=http://api.roundtable.world/v1/admin
    API_KEY=abcdefghijklmnopq
```
