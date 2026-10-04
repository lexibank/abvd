# Releasing ABVD

```shell
git clone https://github.com/lexibank/abvd abvd-cldf
cd abvd-cldf
pip install -e .[test]
```

```shell
cldfbench lexibank.makecldf lexibank_abvd.py --glottolog-version v5.3 --concepticon-version v3.4.0 --clts-version v2.3.0
pytest
```

```shell
cldfbench cldfreadme lexibank_abvd.py
```

```shell
pip install cldfviz[cartopy]
cldfbench cldfviz.map cldf --format svg --height 50 --output map.svg --markersize 70 --padding-left 8 --padding-right 8 --padding-top 3 --padding-bottom 3 --with-ocean --language-properties Family --no-legend --pacific-centered
```
