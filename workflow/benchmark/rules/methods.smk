BASE_METHODS = ("fmlrc", "ratatosk", "lordec")
HERO_METHODS = ("f_hero", "r_hero", "l_hero")
HERO_BASE = {"f_hero": "fmlrc", "r_hero": "ratatosk", "l_hero": "lordec"}
SELF_METHODS = ("vechat", "dechat")
TOOL_OPTIONS = " ".join(
    f"--{name.replace('_', '-')} {config['tools'][name]}"
    for name in ("seqkit", "dadec", "fmlrc", "fmlrc_convert", "ropebwt2",
                 "ratatosk", "lordec", "hero", "hero_python", "colormap",
                 "proovread", "vechat", "dechat")
)

def hero_base_path(wc, filename):
    return f"{WORK}/methods/short_{wc.coverage}/{HERO_BASE[wc.method]}/shared/{filename}"

def external_hero_base_corrected(wc):
    return EXTERNAL_HERO_BASES[(wc.coverage, wc.method)]["corrected"]

def external_hero_base_resources(wc):
    path = EXTERNAL_HERO_BASES[(wc.coverage, wc.method)].get("resources")
    return [path] if path else []

def method_long_input(wc):
    # Zymo coverage labels represent long-read fractions.  Whenever a
    # coverage-specific long-read subsample is configured, every method must
    # receive that subsample; hybrid methods still use the complete
    # short-read input via method_short_input below.
    if wc.coverage in LONG_READ_SUBSAMPLES:
        return f"{WORK}/inputs/long_{wc.coverage}.fa"
    return LONG_FASTA

def method_short_input(wc):
    if wc.method in SELF_METHODS:
        return f"{WORK}/inputs/long_{wc.coverage}.fa"
    return f"{WORK}/inputs/short_{wc.coverage}.fa"

if ALL_MODE:
    rule correct_method:
        input:
            preflight=rules.preflight.output,
            long=method_long_input,
            short=method_short_input,
        output:
            corrected=f"{RESULTS}/short_{{coverage}}/{{method}}/corrected.fa",
            resources=f"{BENCHMARK_OUT}/short_{{coverage}}/{{method}}/resources.time.txt",
        log: f"{LOGS}/short_{{coverage}}/{{method}}.log"
        wildcard_constraints: method="dadec|fmlrc|ratatosk|lordec|colormap|proovread|vechat|dechat"
        threads: config["resources"]["method_threads"]
        params:
            python=config["tools"]["runner_python"], time=config["tools"]["time"], conda=CONDA,
            env=lambda wc: config["environments"]["methods"][wc.method],
            run_dir=lambda wc: f"{WORK}/methods/short_{wc.coverage}/{wc.method}/round1",
            k_values=lambda wc: json.dumps(COVERAGE_PARAMETERS[wc.coverage], sort_keys=True),
            split=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["dadec_split"],
            threshold=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["dadec_threshold"],
            a1=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["dadec_abundance1"],
            a2=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["dadec_abundance2"],
            hero_split=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["hero_split"],
            hero_iterations=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["hero_iterations"],
            lordec_solid=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["lordec_solid"],
        shell:
            r"""
            set -euo pipefail
            mkdir -p {params.run_dir:q} $(dirname {output.corrected:q}) $(dirname {log:q})
            rm -f {output.resources:q}.tmp
            {params.time:q} -f 'wall_seconds=%e\nuser_cpu_seconds=%U\nsystem_cpu_seconds=%S\nmax_rss_kb=%M\nexit_code=%x' \
              -o {output.resources:q}.tmp {params.conda:q} run --no-capture-output -n {params.env:q} \
              {params.python:q} {RUN_METHOD_SCRIPT:q} --method {wildcards.method:q} \
              --long {input.long:q} --short {input.short:q} --output {output.corrected:q} \
              --workdir {params.run_dir:q} --log {log:q} --threads {threads} {TOOL_OPTIONS} \
              --k-values {params.k_values:q} --split {params.split} --threshold {params.threshold} \
              --abundance1 {params.a1} --abundance2 {params.a2} --hero-split {params.hero_split} \
              --hero-iterations {params.hero_iterations} --lordec-solid {params.lordec_solid}
            test -s {output.corrected:q}
            mv {output.resources:q}.tmp {output.resources:q}
            """

    rule continue_base_to_round3:
        input:
            preflight=rules.preflight.output,
            round1=f"{RESULTS}/short_{{coverage}}/{{method}}/corrected.fa",
            short=f"{WORK}/inputs/short_{{coverage}}.fa",
        output:
            corrected=f"{WORK}/methods/short_{{coverage}}/{{method}}/shared/round3.fa",
            resources=f"{WORK}/methods/short_{{coverage}}/{{method}}/shared/round2_3.time.txt",
        log: f"{LOGS}/short_{{coverage}}/{{method}}.round2_3.log"
        wildcard_constraints: method="fmlrc|ratatosk|lordec"
        threads: config["resources"]["method_threads"]
        params:
            python=config["tools"]["runner_python"], time=config["tools"]["time"], conda=CONDA,
            env=lambda wc: config["environments"]["methods"][wc.method],
            run_dir=lambda wc: f"{WORK}/methods/short_{wc.coverage}/{wc.method}/shared/round2_3",
            k_values=lambda wc: json.dumps(COVERAGE_PARAMETERS[wc.coverage], sort_keys=True),
            lordec_solid=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["lordec_solid"],
        shell:
            r"""
            set -euo pipefail
            mkdir -p {params.run_dir:q} $(dirname {output.corrected:q}) $(dirname {log:q})
            rm -f {output.resources:q}.tmp
            {params.time:q} -f 'wall_seconds=%e\nuser_cpu_seconds=%U\nsystem_cpu_seconds=%S\nmax_rss_kb=%M\nexit_code=%x' \
              -o {output.resources:q}.tmp {params.conda:q} run --no-capture-output -n {params.env:q} \
              {params.python:q} {RUN_METHOD_SCRIPT:q} --method {wildcards.method:q} --rounds 2 \
              --long {input.round1:q} --short {input.short:q} --output {output.corrected:q} \
              --workdir {params.run_dir:q} --log {log:q} --threads {threads} {TOOL_OPTIONS} \
              --k-values {params.k_values:q} --lordec-solid {params.lordec_solid}
            test -s {output.corrected:q}
            mv {output.resources:q}.tmp {output.resources:q}
            """

    rule hero_from_shared_round3:
        input:
            preflight=rules.preflight.output,
            long=lambda wc: hero_base_path(wc, "round3.fa"),
            short=f"{WORK}/inputs/short_{{coverage}}.fa",
        output:
            corrected=f"{RESULTS}/short_{{coverage}}/{{method}}/corrected.fa",
            resources=f"{WORK}/methods/short_{{coverage}}/{{method}}/hero_only.time.txt",
        log: f"{LOGS}/short_{{coverage}}/{{method}}.log"
        wildcard_constraints: method="f_hero|r_hero|l_hero"
        threads: config["resources"]["method_threads"]
        params:
            python=config["tools"]["runner_python"], time=config["tools"]["time"], conda=CONDA, env="hero",
            run_dir=lambda wc: f"{WORK}/methods/short_{wc.coverage}/{wc.method}/hero",
            k_values=lambda wc: json.dumps(COVERAGE_PARAMETERS[wc.coverage], sort_keys=True),
            hero_split=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["hero_split"],
            hero_iterations=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["hero_iterations"],
        shell:
            r"""
            set -euo pipefail
            mkdir -p {params.run_dir:q} $(dirname {output.corrected:q}) $(dirname {log:q})
            rm -f {output.resources:q}.tmp
            {params.time:q} -f 'wall_seconds=%e\nuser_cpu_seconds=%U\nsystem_cpu_seconds=%S\nmax_rss_kb=%M\nexit_code=%x' \
              -o {output.resources:q}.tmp {params.conda:q} run --no-capture-output -n {params.env:q} \
              {params.python:q} {RUN_METHOD_SCRIPT:q} --method {wildcards.method:q} --precorrected \
              --long {input.long:q} --short {input.short:q} --output {output.corrected:q} \
              --workdir {params.run_dir:q} --log {log:q} --threads {threads} {TOOL_OPTIONS} \
              --k-values {params.k_values:q} --hero-split {params.hero_split} \
              --hero-iterations {params.hero_iterations}
            test -s {output.corrected:q}
            mv {output.resources:q}.tmp {output.resources:q}
            """

    rule combine_hero_resources:
        input:
            round1=lambda wc: f"{BENCHMARK_OUT}/short_{wc.coverage}/{HERO_BASE[wc.method]}/resources.time.txt",
            round2_3=lambda wc: hero_base_path(wc, "round2_3.time.txt"),
            hero=lambda wc: f"{WORK}/methods/short_{wc.coverage}/{wc.method}/hero_only.time.txt",
        output:
            f"{BENCHMARK_OUT}/short_{{coverage}}/{{method}}/resources.time.txt",
        wildcard_constraints: method="f_hero|r_hero|l_hero"
        params: python=PYTHON, conda=CONDA, env=EVAL_ENV, script=str(SCRIPT_DIR / "combine_resources.py")
        shell:
            "{params.conda:q} run --no-capture-output -n {params.env:q} {params.python:q} "
            "{params.script:q} --inputs {input:q} --output {output:q}"

elif EXTERNAL_HERO_BASES and all((coverage, method) in EXTERNAL_HERO_BASES for coverage, method in METHOD_TARGETS):
    rule continue_external_base_to_round3:
        input:
            preflight=rules.preflight.output,
            round1=external_hero_base_corrected,
            short=f"{WORK}/inputs/short_{{coverage}}.fa",
        output:
            corrected=f"{WORK}/methods/short_{{coverage}}/{{method}}/shared/round3.fa",
            resources=f"{WORK}/methods/short_{{coverage}}/{{method}}/shared/round2_3.time.txt",
        log: f"{LOGS}/short_{{coverage}}/{{method}}.round2_3.log"
        wildcard_constraints: method="f_hero|r_hero|l_hero"
        threads: config["resources"]["method_threads"]
        params:
            python=config["tools"]["runner_python"], time=config["tools"]["time"], conda=CONDA,
            env=lambda wc: config["environments"]["methods"][HERO_BASE[wc.method]],
            base_method=lambda wc: HERO_BASE[wc.method],
            run_dir=lambda wc: f"{WORK}/methods/short_{wc.coverage}/{wc.method}/shared/round2_3",
            k_values=lambda wc: json.dumps(COVERAGE_PARAMETERS[wc.coverage], sort_keys=True),
            lordec_solid=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["lordec_solid"],
        shell:
            r"""
            set -euo pipefail
            mkdir -p {params.run_dir:q} $(dirname {output.corrected:q}) $(dirname {log:q})
            rm -f {output.resources:q}.tmp
            {params.time:q} -f 'wall_seconds=%e\nuser_cpu_seconds=%U\nsystem_cpu_seconds=%S\nmax_rss_kb=%M\nexit_code=%x' \
              -o {output.resources:q}.tmp {params.conda:q} run --no-capture-output -n {params.env:q} \
              {params.python:q} {RUN_METHOD_SCRIPT:q} --method {params.base_method:q} --rounds 2 \
              --long {input.round1:q} --short {input.short:q} --output {output.corrected:q} \
              --workdir {params.run_dir:q} --log {log:q} --threads {threads} {TOOL_OPTIONS} \
              --k-values {params.k_values:q} --lordec-solid {params.lordec_solid}
            test -s {output.corrected:q}
            mv {output.resources:q}.tmp {output.resources:q}
            """

    rule hero_from_external_round3:
        input:
            preflight=rules.preflight.output,
            long=f"{WORK}/methods/short_{{coverage}}/{{method}}/shared/round3.fa",
            short=f"{WORK}/inputs/short_{{coverage}}.fa",
        output:
            corrected=f"{RESULTS}/short_{{coverage}}/{{method}}/corrected.fa",
            resources=f"{WORK}/methods/short_{{coverage}}/{{method}}/hero_only.time.txt",
        log: f"{LOGS}/short_{{coverage}}/{{method}}.log"
        wildcard_constraints: method="f_hero|r_hero|l_hero"
        threads: config["resources"]["method_threads"]
        params:
            python=config["tools"]["runner_python"], time=config["tools"]["time"], conda=CONDA, env="hero",
            run_dir=lambda wc: f"{WORK}/methods/short_{wc.coverage}/{wc.method}/hero",
            k_values=lambda wc: json.dumps(COVERAGE_PARAMETERS[wc.coverage], sort_keys=True),
            hero_split=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["hero_split"],
            hero_iterations=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["hero_iterations"],
        shell:
            r"""
            set -euo pipefail
            mkdir -p {params.run_dir:q} $(dirname {output.corrected:q}) $(dirname {log:q})
            rm -f {output.resources:q}.tmp
            {params.time:q} -f 'wall_seconds=%e\nuser_cpu_seconds=%U\nsystem_cpu_seconds=%S\nmax_rss_kb=%M\nexit_code=%x' \
              -o {output.resources:q}.tmp {params.conda:q} run --no-capture-output -n {params.env:q} \
              {params.python:q} {RUN_METHOD_SCRIPT:q} --method {wildcards.method:q} --precorrected \
              --long {input.long:q} --short {input.short:q} --output {output.corrected:q} \
              --workdir {params.run_dir:q} --log {log:q} --threads {threads} {TOOL_OPTIONS} \
              --k-values {params.k_values:q} --hero-split {params.hero_split} \
              --hero-iterations {params.hero_iterations}
            test -s {output.corrected:q}
            mv {output.resources:q}.tmp {output.resources:q}
            """

    rule combine_external_hero_resources:
        input:
            round1=external_hero_base_resources,
            round2_3=f"{WORK}/methods/short_{{coverage}}/{{method}}/shared/round2_3.time.txt",
            hero=f"{WORK}/methods/short_{{coverage}}/{{method}}/hero_only.time.txt",
        output:
            f"{BENCHMARK_OUT}/short_{{coverage}}/{{method}}/resources.time.txt",
        wildcard_constraints: method="f_hero|r_hero|l_hero"
        params: python=PYTHON, conda=CONDA, env=EVAL_ENV, script=str(SCRIPT_DIR / "combine_resources.py")
        shell:
            "{params.conda:q} run --no-capture-output -n {params.env:q} {params.python:q} "
            "{params.script:q} --inputs {input:q} --output {output:q}"

else:
    rule correct_method:
        input:
            preflight=rules.preflight.output,
            long=method_long_input,
            short=method_short_input,
        output:
            corrected=f"{RESULTS}/short_{{coverage}}/{{method}}/corrected.fa",
            resources=f"{BENCHMARK_OUT}/short_{{coverage}}/{{method}}/resources.time.txt",
        log: f"{LOGS}/short_{{coverage}}/{{method}}.log"
        threads: config["resources"]["method_threads"]
        params:
            python=config["tools"]["runner_python"], time=config["tools"]["time"], conda=CONDA,
            env=lambda wc: config["environments"]["methods"][wc.method],
            run_dir=lambda wc: f"{WORK}/methods/short_{wc.coverage}/{wc.method}",
            k_values=lambda wc: json.dumps(COVERAGE_PARAMETERS[wc.coverage], sort_keys=True),
            split=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["dadec_split"],
            threshold=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["dadec_threshold"],
            a1=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["dadec_abundance1"],
            a2=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["dadec_abundance2"],
            hero_split=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["hero_split"],
            hero_iterations=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["hero_iterations"],
            lordec_solid=lambda wc: COVERAGE_PARAMETERS[wc.coverage]["lordec_solid"],
        shell:
            r"""
            set -euo pipefail
            mkdir -p {params.run_dir:q} $(dirname {output.corrected:q}) $(dirname {log:q})
            rm -f {output.resources:q}.tmp
            {params.time:q} -f 'wall_seconds=%e\nuser_cpu_seconds=%U\nsystem_cpu_seconds=%S\nmax_rss_kb=%M\nexit_code=%x' \
              -o {output.resources:q}.tmp {params.conda:q} run --no-capture-output -n {params.env:q} \
              {params.python:q} {RUN_METHOD_SCRIPT:q} --method {wildcards.method:q} \
              --long {input.long:q} --short {input.short:q} --output {output.corrected:q} \
              --workdir {params.run_dir:q} --log {log:q} --threads {threads} {TOOL_OPTIONS} \
              --k-values {params.k_values:q} --split {params.split} --threshold {params.threshold} \
              --abundance1 {params.a1} --abundance2 {params.a2} --hero-split {params.hero_split} \
              --hero-iterations {params.hero_iterations} --lordec-solid {params.lordec_solid}
            test -s {output.corrected:q}
            mv {output.resources:q}.tmp {output.resources:q}
            """
