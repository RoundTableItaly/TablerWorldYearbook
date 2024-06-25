# TablerWorldYearbook

TablerWorldYearbook

![Screenshot](docs/screenshot-01.png "Screenshot")

## How to use

Download the latest release and install the dependencies for [WeasyPrint for Windows](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).

## Install

    pipenv install

## Update

    pipenv update

## Run

    pipenv run python .\main.py

## Build exe

    pipenv run pyinstaller -y TablerWorldYearbook.spec

## settings.json

Get the API key from the menu Settings > API tokens.

    API_BASE_URL=http://api.roundtable.world/v1/admin
    API_KEY=abcdefghijklmnopq
