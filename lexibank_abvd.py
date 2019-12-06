# coding=utf-8
import re
from pathlib import Path

from clldutils.misc import slug
from pybtex.database import parse_string  # dependency of pycldf, so should be installed.
from pylexibank.providers import abvd
from pylexibank.util import progressbar
from pylexibank import FormSpec


class Dataset(abvd.BVD):
    dir = Path(__file__).parent
    id = 'abvd'
    SECTION = 'austronesian'
    
    invalid_ids = [
        261,  # Duplicate West Futuna list
    ]
    
    max_language_id = 2000

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
        for wl in progressbar(self.iter_wordlists(args.log), desc="cldfify"):
            wl.to_cldf(args.writer, concepts)
