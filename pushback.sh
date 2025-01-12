#!/bin/bash
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add .
git commit -m "[CI] Convert xlsx to json"
git push