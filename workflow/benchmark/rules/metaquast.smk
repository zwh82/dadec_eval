if EXTERNAL_REPORT is not None:
    rule import_metaquast_report:
        input: report=EXTERNAL_REPORT
        output: f"{RESULTS}/short_{{coverage}}/{{method}}/metaquast.ambiguity9999/combined_reference/report.tsv"
        log: f"{LOGS}/short_{{coverage}}/{{method}}.metaquast.ambiguity9999.log"
        shell:
            r"""
            set -euo pipefail
            if test -s {output:q} && test {output:q} -nt {input.report:q}; then
              echo "Existing imported combined-reference report is current; skipping copy."
              exit 0
            fi
            mkdir -p $(dirname {output:q}) $(dirname {log:q})
            cp {input.report:q} {output:q}
            test -s {output:q}
            """

elif EVALUATION_TOOL == "metaquast":
    rule metaquast_corrected:
        input: reads=corrected_fasta_input, reference=REFERENCE
        output: f"{RESULTS}/short_{{coverage}}/{{method}}/{{evaluation}}/combined_reference/report.tsv"
        log: f"{LOGS}/short_{{coverage}}/{{method}}.{{evaluation}}.log"
        threads: config["resources"]["metaquast_threads"]
        params: executable=config["tools"]["metaquast"], conda=CONDA, env=EVAL_ENV,
                python=PYTHON, cleanup_script=COMPACT_QUAST_SCRIPT,
                cleanup_threshold=QUAST_CLEANUP_THRESHOLD_MIB,
                outdir=lambda wc: f"{RESULTS}/short_{wc.coverage}/{wc.method}/{wc.evaluation}",
                ambiguity_usage=config["metaquast"]["ambiguity_usage"],
                ambiguity_score=lambda wc: EVALUATION_DIR_TO_SCORE[wc.evaluation],
                min_contig=config["metaquast"]["min_contig"],
                extra=config["metaquast"]["extra_args"]
        shell:
            r"""
            set -euo pipefail
            if test -s {output:q} && test {output:q} -nt {input.reads:q} && test {output:q} -nt {input.reference:q}; then
              echo "Existing combined-reference report is current; skipping MetaQUAST evaluation."
              exit 0
            fi
            mkdir -p $(dirname {log:q}) $(dirname {params.outdir:q})
            tmpdir=$(mktemp -d {params.outdir:q}.tmp.XXXXXX)
            trap 'rm -rf "$tmpdir" || true' EXIT
            {params.conda:q} run --no-capture-output -n {params.env:q} {params.executable:q} -r {input.reference:q} -t {threads} \
              --ambiguity-usage {params.ambiguity_usage:q} --ambiguity-score {params.ambiguity_score} \
              --min-contig {params.min_contig} {params.extra} -o "$tmpdir" {input.reads:q} > {log:q} 2>&1
            test -s "$tmpdir/combined_reference/report.tsv"
            {params.conda:q} run --no-capture-output -n {params.env:q} {params.python:q} {params.cleanup_script:q} \
              --root "$tmpdir" --threshold-mib {params.cleanup_threshold} --apply \
              --manifest "$tmpdir/cleanup.json"
            rm -rf {params.outdir:q}
            mv "$tmpdir" {params.outdir:q}
            trap - EXIT
            test -s {output:q}
            """

else:
    rule quast_corrected:
        input: reads=corrected_fasta_input, reference=REFERENCE
        output: f"{RESULTS}/short_{{coverage}}/{{method}}/{{evaluation}}/report.tsv"
        log: f"{LOGS}/short_{{coverage}}/{{method}}.{{evaluation}}.log"
        threads: config["resources"]["metaquast_threads"]
        params: executable=config["tools"]["quast"], conda=CONDA, env=EVAL_ENV,
                python=PYTHON, cleanup_script=COMPACT_QUAST_SCRIPT,
                cleanup_threshold=QUAST_CLEANUP_THRESHOLD_MIB,
                outdir=lambda wc: f"{RESULTS}/short_{wc.coverage}/{wc.method}/{wc.evaluation}",
                min_contig=config["quast"]["min_contig"], extra=config["quast"]["extra_args"]
        shell:
            r"""
            set -euo pipefail
            if test -s {output:q} && test {output:q} -nt {input.reads:q} && test {output:q} -nt {input.reference:q}; then
              echo "Existing report is current; skipping QUAST evaluation."
              exit 0
            fi
            mkdir -p $(dirname {log:q}) $(dirname {params.outdir:q})
            tmpdir=$(mktemp -d {params.outdir:q}.tmp.XXXXXX)
            trap 'rm -rf "$tmpdir" || true' EXIT
            {params.conda:q} run --no-capture-output -n {params.env:q} {params.executable:q} \
              -r {input.reference:q} -t {threads} --min-contig {params.min_contig} \
              {params.extra} {input.reads:q} -o "$tmpdir" > {log:q} 2>&1
            test -s "$tmpdir/report.tsv"
            {params.conda:q} run --no-capture-output -n {params.env:q} {params.python:q} {params.cleanup_script:q} \
              --root "$tmpdir" --threshold-mib {params.cleanup_threshold} --apply \
              --manifest "$tmpdir/cleanup.json"
            rm -rf {params.outdir:q}
            mv "$tmpdir" {params.outdir:q}
            trap - EXIT
            test -s {output:q}
            """
