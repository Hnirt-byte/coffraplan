#!/bin/sh
# Contrôle de syntaxe du script de l'application
T=$(mktemp --suffix=.js)
python3 -c "
import sys;s=open(sys.argv[1]).read();a=s.index('<script>')+8;b=s.index('</script>',a);open(sys.argv[2],'w').write(s[a:b])" "${1:-$(dirname "$0")/../app/CoffraPlan.html}" "$T" && node --check "$T" && echo "syntaxe OK"
# Module d'import de plans (hors appli, modules/import)
for f in "$(dirname "$0")"/../modules/import/*.js; do node --check "$f" || exit 1; done && echo "syntaxe modules/import OK"
