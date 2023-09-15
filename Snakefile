import torch


## preprocess optional arguments
if config["preprocess_gpu"]:
    preprocess_gpu="-g"
else:
    preprocess_gpu = ""

if config["additional_rules"]:
    additional_rules=config["additional_rules"]
else:
    additional_rules = ""


rule post_process:
    input:
        pass


rule preprocess:
    input:
        notes=config["notes"],
        outname=temp("{}/preprocessed_notes.tsv".format(config["outdir"])),
    output:
        pre_processed=temp("{}/preprocessed_notes.tsv".format(config["outdir"]))
    shell:
        """
        python scripts/preprocess/preprocess.py -n input.notes -o input.outname {} {}
        """.format(preprocess_gpu, additional_rules)

rule inference:
    input:
        notes=rules.preprocess.output.pre_processed,
        outname=config["{}/inferred_notes".format(config["outdir"])],
        device= config["inference_device"] if "inference_device" in config.keys() else (torch.device('cuda' if torch.cuda.is_available() else 'cpu')),
        classification_model=config["classification_model"],
        summarization_model=config["summarization_model"],
        distance_model=config["distance_model_name"],
        distance_cache=config["distance_model_cache"],
        cutoff=config["prob_cutoff"],
        use_chirpp=config["use_chirpp"]
    output:
        inferred_notes=temp("{}/inferred_notes".format(config["outdir"]))
    shell:
        """
        python scripts/inference/inference.py -n input.notes -o input.outname -d input.device -c input.classification_model \
            -s input.summarization_model --distance_model_name input.distance_model --distance_model_dir input.distance_cache \
            --cutoff input.cutoff --use_chirpp input.use_chirpp
        """



