# Drosophila assembly execution

Run every command from this directory:

```bash
cd /home/work/wenhai/dadec/benchmark/work_scripts/assembly
./run.sh -n --printshellcmds
./run.sh --printshellcmds
```

For a run that survives terminal disconnection, start the user service and
follow the shared log:

```bash
./start.sh
tail -f workflow.log
```

The service name is `dadec-drosophila-assembly.service`.

The workflow is restartable. Canu and hifiasm receive the configured FASTAs and
run with strictly 64 threads. Canu follows the reference invocation with
`-p canu ... -pacbio INPUT` and does not add `-corrected`; its state is kept in
each result cell's fresh `work_pacbio/` directory. Hifiasm state is kept in
`work_corrected/`.

Inspect progress and verify the completed assembly matrix with:

```bash
./status.sh
./verify.sh
```

The configuration is
`benchmark/config/runs/drosophila/assembly/config.yaml`. `threads` must be 64
and controls Canu and hifiasm. `quast_threads` is independent (currently 64)
because evaluation does not need the assembler-only strictness. The launcher
gives Snakemake 64 total cores.

To skip an assembler that cannot produce an assembly for one input, set
`skip_assemblers` (and optionally `skip_reasons`) for that method in the
configuration. Skipped cells are excluded from QUAST and recorded in
`manifest.json`; the remaining cells continue normally.

Updating the configuration to reorder methods or change skip settings reruns
preflight and the lightweight summary only. Existing assembly and QUAST
outputs are not invalidated. To intentionally rebuild a completed cell after
changing its source or tool parameters, request that target explicitly with
Snakemake's `--forcerun` option.
