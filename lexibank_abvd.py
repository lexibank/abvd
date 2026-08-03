import re
import dataclasses
from pathlib import Path
from typing import Optional

from nameparser import HumanName
import pycldf
from clldutils.misc import slug
from pylexibank.providers import abvd
from pylexibank import FormSpec, Concept


@dataclasses.dataclass
class ABVDConcept(Concept):
    Category: Optional[str] = None


def normalize_contributors(l):
    for key in ['checkedby', 'typedby']:
        l[key] = normalize_names(l[key])
    return l


def normalize_names(names):
    res = []
    if names:
        for name in re.split(r'\s+and\s+|\s*&\s*|,\s+|\s*\+\s*', names):
            name = {
                'Simon': 'Simon Greenhill',
                'D. Mead': 'David Mead',
                'Alex François': 'Alexandre François',
                'Dr Alex François': 'Alexandre François',
                'R. Blust': 'Robert Blust',
            }.get(name, name)
            name = HumanName(name.title())
            res.append(f'{name.first or name.title} {name.last}'.strip())
    return ' and '.join(res)


class Dataset(abvd.BVD):
    dir = Path(__file__).parent
    id = 'abvd'
    SECTION = 'austronesian'
    concept_class = ABVDConcept
    
    invalid_ids = [
        261,  # Duplicate West Futuna list
    ]
    
    language_ids = list(range(1, 2500))

    form_spec = FormSpec(
        brackets={"[": "]", "{": "}", "(": ")"},
        separators=";/,~",
        missing_data=('-', ),
        strip_inside_brackets=True,
    )

    def cmd_makecldf(self, args):
        args.writer.add_sources(*self.etc_dir.read_bib())
        concepts = args.writer.add_concepts(
            id_factory=lambda c: c.id.split('-')[-1]+ '_' + slug(c.english),
            lookup_factory=lambda c: c['ID'].split('_')[0]
        )
        for wl in self.iter_wordlists(args.log):
            wl.to_cldf(args.writer, concepts)
            # Now normalize the typedby and checkedby values:
            args.writer.objects['LanguageTable'][-1] = normalize_contributors(
                args.writer.objects['LanguageTable'][-1])

        # Add more coordinates, for dialects and proto-languages using the data from glottolog-cldf:
        p = args.glottolog.api.path().parent / 'glottolog-cldf' / 'cldf' / 'cldf-metadata.json'
        if not p.exists():
            return
        glangs = {
            lg['ID']: lg for lg in pycldf.Dataset.from_metadata(p).iter_rows(
                'LanguageTable', 'id', 'latitude', 'longitude')}
        for lg in args.writer.objects['LanguageTable']:
            if lg['Glottocode']:
                if lg['Glottocode'] in glangs:
                    if not lg['Latitude']:
                        lg['Latitude'] = glangs[lg['Glottocode']]['Latitude']
                        lg['Longitude'] = glangs[lg['Glottocode']]['Longitude']
                else:
                    args.log.warning('Invalid Glottocode: %s', lg['Glottocode'])
                    lg['Glottocode'] = None
