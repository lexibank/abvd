import re
import collections
import dataclasses
from pathlib import Path
from typing import Optional

from nameparser import HumanName
import pycldf
from clldutils.misc import slug
from pylexibank.providers import abvd
from pylexibank import FormSpec, Concept

WORD_NOTES = {
    "8": ("to turn", "veer to the side, as in turning left"),
    "13": ("back", "body part"),
    "26": ("hair", "of the head"),
    "38": ("to chew", "A: general term; B: chew betel"),
    "39": ("to cook", "A: general term; B: boil food"),
    "49": ("to lie down", "to sleep"),
    "67": ("to sew", "clothing"),
    "69": ("to hunt", "for game"),
    "70": ("to shoot", "an arrow"),
    "72": ("to hit", "with stick, club"),
    "77": ("to scratch", "an itch"),
    "78": ("to cut, hack", "wood"),
    "80": ("to split", "transitive"),
    "83": ("to work", "in garden, field"),
    "86": ("to grow", "intransitive"),
    "87": ("to swell", "as an abcess"),
    "88": ("to squeeze", "as juice from a fruit"),
    "89": ("to hold", "in the fist"),
    "93": ("to pound, beat", "as rice or prepared food"),
    "94": ("to throw", "as a stone"),
    "95": ("to fall", "as a fruit"),
    "108": ("louse", "A: general term, B: head louse"),
    "112": ("rotten", "of food, or corpse"),
    "113": ("branch", "the branch itself, not the fork of the branch"),
    "122": ("water", "fresh water"),
    "131": ("cloud", "white cloud, not a rain cloud"),
    "137": ("to blow", "A: of the wind, B: with the mouth"),
    "138": ("warm", "of weather"),
    "139": ("cold", "of weather"),
    "140": ("dry", "A: general term, B: to dry up"),
    "144": ("to burn", "transitive"),
    "145": ("smoke", "of a fire"),
    "154": ("short", "A: in height, B: in length"),
    "155": ("long", "of objects"),
    "156": ("thin", "of objects"),
    "157": ("thick", "of objects"),
    "162": ("old", "of people"),
    "170": ("when?", "question"),
    "171": ("to hide", "intransitive"),
    "172": ("to climb", "A: ladder, B: mountain"),
    "181": ("where?", "question"),
    "185": ("we", "A: inclusive, B: exclusive"),
    "188": ("what?", "question"),
    "189": ("who?", "question"),
    "194": ("how?", "question"),
    "197": ("One", "1"),
    "198": ("Two", "2"),
    "199": ("Three", "3"),
    "200": ("Four", "4"),
    "201": ("Five", "5"),
    "202": ("Six", "6"),
    "203": ("Seven", "7"),
    "204": ("Eight", "8"),
    "205": ("Nine", "9"),
    "206": ("Ten", "10"),
    "207": ("Twenty", "20"),
    "208": ("Fifty", "50"),
    "209": ("One Hundred", "100"),
    "210": ("One Thousand", "1,000"),
}


@dataclasses.dataclass
class ABVDConcept(Concept):
    Category: Optional[str] = None
    Comment: Optional[str] = None


def normalize_contributors(l):
    if not l['Contributor'] and l['Source_Comment'] and 'Ennever' in l['Source_Comment']:
        l['Contributor'] = l['Source_Comment']
    for key in ['checkedby', 'Contributor']:
        l[key] = normalize_names(l[key])
    return l


def normalize_names(names):
    res = []
    if names:
        names = {
            'INAGAKI, Kazuya': 'Kazuya Inagaki',
            'Simon Greenhill/Mary Walworth': 'Simon Greenhill and Mary Walworth',
        }.get(names, names)
        for name in re.split(r'\s+and\s+|\s*&\s*|,\s+|\s*\+\s*', names):
            name = {
                'Simon': 'Simon Greenhill',
                'D. Mead': 'David Mead',
                'Andrew C. Hsiu': 'Andrew Hsiu',
                'Alex François': 'Alexandre François',
                'Dr Alex François': 'Alexandre François',
                'R. Blust': 'Robert Blust',
                'Jacques Guillaume': 'Guillaume Jacques',
                'Lana. Takau': 'Lana Takau',
                'Sander Adelaar': 'Alexander Adelaar',
            }.get(name, name)
            name = HumanName(name.title())
            res.append(re.sub(
                r'\s+',
                ' ',
                f'{name.first or name.title} {name.middle} {name.last}'.strip()))
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
        args.writer.cldf.add_component(
            'ContributionTable',
            'Source_Comment',
            'checkedby',
            'problems',
            {'name': 'Language_ID', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#languageReference'},
            {'name': 'Source', 'separator': ';', 'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source'},
        )
        for col in ['Description', 'problems']:
            args.writer.cldf['ContributionTable', col].common_props['dc:format'] = 'text/markdown'
        lid2src = collections.defaultdict(list)
        args.writer.add_sources(*self.etc_dir.read_bib())
        for src in args.writer.cldf.sources:
            for lid in src.get('wordlist_ids', '').split():
                lid2src[lid].append(src.id)

        concepts = args.writer.add_concepts(
            id_factory=lambda c: c.id.split('-')[-1]+ '_' + slug(c.english),
            lookup_factory=lambda c: c['ID'].split('_')[0]
        )
        for c in args.writer.objects['ParameterTable']:
            nid, label = c['ID'].split('_')
            if nid in WORD_NOTES:
                l, comment = WORD_NOTES[nid]
                assert slug(l) == label, (l, label, comment)
                c['Comment'] = comment
                del WORD_NOTES[nid]
        assert not WORD_NOTES, WORD_NOTES

        langs = {}
        for wl in self.iter_wordlists(args.log):
            lid = (wl.language.name, wl.language.glottocode)
            if lid not in langs:
                args.writer.add_language(
                    ID=wl.language.id,
                    Glottocode=wl.language.glottocode,
                    ISO639P3code=wl.language.iso,
                    Name=wl.language.name,
                )
                langs[lid] = wl.language.id
            self.wordlist_to_cldf(args.writer, langs[lid], wl, concepts, lid2src.get(wl.language.id, []))

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

    def wordlist_to_cldf(self, writer, lid, wl, concepts, sources):
        writer.objects['ContributionTable'].append(normalize_contributors(dict(
            ID=wl.language.id,
            Name=wl.language.name,
            Language_ID=lid,
            Source_Comment=wl.language.author,
            Description=wl.language.notes,
            Contributor=wl.language.typedby,
            checkedby=wl.language.checkedby,
            problems=wl.language.problems,
            Source=sources,
        )))

        for entry in wl.entries:
            if entry.name is None or len(entry.name) == 0:  # skip empty entries
                continue  # pragma: no cover

            # mark entries marked as incorrect word form due to semantics
            # (x = probably, s = definitely)
            cognacy_comment = None
            if entry.cognacy and entry.cognacy.lower() in ('s', 'x'):
                cognacy_comment = entry.cognacy.lower()
                entry.cognacy = None

            loanbool = bool('l' in (entry.loan or "").lower())
            lex = writer.add_forms_from_value(
                Local_ID=entry.id,
                Language_ID=lid,
                Contribution_ID=wl.language.id,
                Parameter_ID=concepts.get(entry.word_id),
                Value=entry.name,
                Source=sources,
                Cognacy=entry.cognacy,
                Cognacy_Comment=cognacy_comment,
                Comment=entry.comment or '',
                Loan=loanbool,
                Loan_Raw=f'{"L" if loanbool else ""}{"?" if "?" in (entry.loan or "") else ""}',
            )
            if lex:
                for cognate_set_id in entry.cognates:
                    match = wl.dataset.cognate_pattern.match(cognate_set_id)
                    assert match
                    # make global cognate set id
                    writer.add_cognate(
                        lexeme=lex[0],
                        Cognateset_ID=f"{slug(entry.word)}-{match.group('id')}",
                        Doubt=bool(match.group('doubt')),
                        Source=['Greenhilletal2008'],
                    )
