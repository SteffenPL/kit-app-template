#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$(dirname "$0")/pdfs"

curl -L \
  "https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1008160&type=printable" \
  -o "$(dirname "$0")/pdfs/maxian-2020-computational-estimates-cell-migration-ecm.pdf"

curl -L \
  "https://cims.nyu.edu/~mogilner/actin.pdf" \
  -o "$(dirname "$0")/pdfs/mogilner-oster-1996-cell-motility-driven-by-actin-polymerization.pdf"

