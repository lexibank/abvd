# coding=utf-8
from __future__ import unicode_literals, print_function
from itertools import groupby

from clldutils.path import Path
from pylexibank.providers import abvd
from pylexibank.dataset import Metadata
from pylexibank.util import pb


class Dataset(abvd.BVD):
    dir = Path(__file__).parent
    SECTION = 'austronesian'

    def cmd_install(self, **kw):
        concept_map = {
            c.attributes['url'].unsplit().split('v=')[1]: c.concepticon_id
            for c in self.conceptlist.concepts.values()}

        l_map = {int(l['ID']): l['GLOTTOCODE'] for l in self.languages if l['GLOTTOCODE']}
        bibs = self.dir.read_bib()

        # could do this in one line, but readability loses.
        refs = {}
        sources = self.dir.read_tsv('sources.tsv')
        for key, group in groupby(sources, lambda x: x[0]):
            refs['austronesian-%s' % key] = [g for (k, g) in group]

        with self.cldf as ds:
            for wl in pb(list(self.iter_wordlists(l_map)), desc='wl-to-cldf'):
                wl.to_cldf(
                    ds,
                    concept_map,
                    citekey=";".join(refs.get(wl.id, [])),
                    source=[b for b in bibs if b.id in refs.get(wl.id, [])]
                )
