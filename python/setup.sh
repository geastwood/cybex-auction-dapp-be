#!/usr/bin/bash

pip install virtualenv
virtualenv .venv

source .venv/bin/activate
pip install -r requirements.txt

python import_test_accounts.py

mkdir -p db
mkdir -p bid
