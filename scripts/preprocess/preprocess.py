import os
import argparse as arg

from medspacy.section_detection import SectionRule

from utils import SectionRemover, Preprocess
import params

parser = arg.ArgumentParser(description='Preprocess notes file for inference')
parser.add_argument('-n', '--notes', type=str, help='Path to raw patient notes')
parser.add_argument('-o', '--outname', type=str, help='Path to outputs')
parser.add_argument('-g', '--use_gpu', type=bool, help='whether to use gpu, default False', default=False,
                    action="store_true")
parser.add_argument('--additional_rules', type=str, help="additional rules json file for section remover", default=None)
args = parser.parse_args()


if args.additional_rules is not None:
    additional_rules=SectionRule.from_json(args.additional_rules)
else:
    additional_rules=None


section_remover_for_inference=SectionRemover(lang_model=params.lang_model, remove_sections=params.remove_sections,
                               keep_sections=params.inference_sections, rules_json=params.section_rules,
                               additional_rules=additional_rules, gpu=args.use_gpu)

section_remover_for_autofill=SectionRemover(lang_model=params.lang_model, remove_sections=params.remove_sections,
                               keep_sections=params.autofill_sections, rules_json=params.section_rules,
                               additional_rules=additional_rules, gpu=args.use_gpu)


preprocessed_notes=Preprocess(args.notes, params.note_types, params.terms_to_fix).\
    read_raw_notes(additional_columns=params.include_cols, filters=params.note_types)

inference_notes=preprocessed_notes.merge_notes(section_remover_for_inference, params.include_cols,
                                               params.group_cols, params.orientation, True)

# this need to contain only sections that are related to presenting illness not treatment
# so the rest of the autofill codes do not get confused
autofill_notes=preprocessed_notes.merge_notes(section_remover_for_inference, params.include_cols,
                                               params.group_cols, params.orientation, False)

inference_notes.to_csv("inference_{}".format(args.outname), **params.write_args)
autofill_notes.to_csv("autofill_{}".format(args.outname), **params.write_args)

