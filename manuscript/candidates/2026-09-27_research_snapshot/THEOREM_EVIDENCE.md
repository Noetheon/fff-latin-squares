# Current Edition: Evidence Map

The cutoff is C251. A record check, a fresh finite computation, a written proof
and independent expert review are distinct. The last has not been obtained.

| Topic | Shipped evidence | Review boundary |
| --- | --- | --- |
| FFF12 disproves C38; FFF14/36/98 exist | [FFF12 table](evidence/data/order12_first.json) and companion files in `evidence/data/` | All line pairs freshly scanned by two algorithms; printed FFF12 table compared exactly. |
| Affine criterion and prime-successor constructions | [Proof](evidence/proofs/fff_affine_prime_successor_bound.md) and manuscript section 09 | Written proof and 253 finite parameter controls; external Katz theorem cited, no novelty claim. |
| Product spectrum and 514 source classes | [Proof](evidence/proofs/fff_three_view_cycle_spectrum_product.md), [trade audit](evidence/runs/2026-09-26_fff20_steiner_trade_mainclasses/results/trade_mainclass_audit.json) | 1024 masks give exactly 512 classes within this family; two further controls yield a global lower bound, not a census. |
| Row-fibred pattern equality | [Proof](evidence/proofs/fff_row_fibred_extension.md) | All three views, 16 finite controls; no unconstrained product cancellation. |
| Quotient descent and intrinsic layers | [Proof](evidence/proofs/fff_binary_quotient_descent_and_dyadic_class_growth.md) | Hypotheses include quotient-free source fibres; order-20 application uses C157. |
| Affine-orbit class counts | [Proof](evidence/proofs/fff_affine_orbit_fibre_classification.md), [finite record](evidence/runs/2026-09-26_fff_affine_orbit_fibres/results/affine_orbit_fibres_audit.json) | Exact group enumeration/Burnside calculations; two FFF160 controls; not a higher-order census. |
| Coloring encoding | [Proof](evidence/proofs/fff_position_value_coloring_channel.md) | 672 finite pair truth tables and negative controls; solver performance is not an obstruction theorem. |
| 14-case normalization | [Proof](evidence/proofs/fff18_same_sign_row1_normal_form.md), [cases](evidence/runs/2026-09-26_fff18_same_sign_row1_split/results/n18_same_sign_row1_cases.json) | Lossless split, not exclusion of every case. |
| C221 restricted translation family | [Proof](evidence/proofs/fff18_case2_conditional_lex_symmetry.md), [coverage record](evidence/runs/2026-09-24_fff18_case2_lex_symmetry/results/family_exclusion_audit.json), [certificate metadata](evidence/runs/2026-09-24_fff18_case2_lex_symmetry/results/p17_case2_full_nonaffine_lex_certification.json) | Historical checks, not rerun or complete proof payloads in this export. |
| C225 cyclic order-17 base, arbitrary transversal | [Proof](evidence/proofs/fff_prime_cyclic_one_point_direction_rigidity.md) | Written direction-bound argument in full manuscript; not arbitrary order-17 bases. |
| C235 odd-map base family | [Proof](evidence/proofs/fff_onepoint_odd_base_transversal_filter.md), [orbit record](evidence/runs/2026-09-25_fff18_onepoint_odd_base_transversal/results/odd_base_uoc_orbits.json), [certificate metadata](evidence/runs/2026-09-25_fff18_onepoint_odd_base_transversal/results/oldold_unsat_certification.json) | Only the stated 12,513 bases; original proofs not freshly checked. |
| C251 fixed-remainder contractions | [Proof](evidence/proofs/fff20_represented_class_contraction_screen.md), [finite record](evidence/runs/2026-09-27_fff20_trade_contraction_screen/results/trade_contraction_status.json) | Only the original 514 represented source classes and specified contraction model. |
| Five-cell conflict | [Proof](evidence/proofs/fff18_five_cell_view_lattice.md), [view-lattice record](evidence/runs/2026-09-27_fff18_five_cell_view_lattice/results/view_lattice_status.json), [certificate metadata](evidence/runs/2026-09-27_fff18_five_cell_view_lattice/results/full_certified.json) | One fixed context, not a whole row-1 case or unrestricted order 18. |

Order-8 census completeness and the order-10 exhaustive reduction/master records
remain inherited dependencies, discussed in the full report and root
[reproducibility guide](../../../REPRODUCIBILITY.md). The independent finite
checker in this package does not certify those entire historical searches.
