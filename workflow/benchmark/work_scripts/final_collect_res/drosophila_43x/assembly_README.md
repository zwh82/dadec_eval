# Drosophila 43x assembly result collection

Run:

```bash
bash benchmark/work_scripts/final_collect_res/drosophila_43x/collect_assembly_results.sh
```

The collector reads only assembly-local QUAST reports under
`benchmark/runs/drosophila_43x/assembly`. It writes separate hifiasm and Canu
tables under `benchmark/results/drosophila_43x/assembly/`. Missing QUAST reports
are retained as explicit missing rows. The current main-text comparison uses
hifiasm; Canu results are retained separately for supplementary reporting.

The current hifiasm collection contains complete QUAST reports for DADEC,
FMLRC, F_HERO, Ratatosk, R_HERO, LoRDEC and L_HERO. CoLoRMap and Proovread
have resource logs or directories but no assembly QUAST report, so they remain
explicitly marked as missing. The DADEC hifiasm report currently gives 28.59
mismatches per 100 kbp, 22.59 indels per 100 kbp, 73.673% genome fraction,
353 misassemblies, NGA50 60,459 kbp and 4,026 contigs.
