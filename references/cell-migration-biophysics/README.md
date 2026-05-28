# Cell Migration Biophysics References

This folder collects references for a first Omniverse/Warp prototype of a migrating cell on a substrate.

The intended model is an overdamped visual-mechanical scaffold:

- deformable cortex/membrane shell
- viscous-drag cytoplasm approximation
- elastic nucleus
- contractile cytoskeletal fibers
- discrete cell-matrix adhesions to a substrate
- optional later upgrade to NVIDIA Warp kernels for explicit force updates

## Suggested Reading Order

1. `reading-notes.md` - short implementation-facing notes.
2. `to-download.md` - papers and docs to download or save manually.
3. `bibliography.bib` - citation records for papers/docs that matter.
4. `pdfs/` - place downloaded open-access PDFs here.

## Prototype Framing

The first prototype should avoid full fluid-structure interaction. A defensible starting equation is overdamped force balance:

```text
drag_i * dx_i/dt = F_elastic + F_contractile + F_adhesion + F_repulsion + F_volume + F_protrusion
```

The scientific goal is not quantitative prediction yet. The first goal is to make the force pathways explicit enough that later refinements have a clear place to attach.

## Component Mapping

| Biological component | First prototype representation | Later refinement |
| --- | --- | --- |
| Cell membrane/cortex | Closed mesh or particles connected by springs | Active cortical shell, area/volume constraints |
| Cytoplasm | Viscous drag plus volume preservation | Poroviscous or fluid-structure model |
| Nucleus | Stiffer internal ellipsoid/sphere with drag | Deformable nucleus with nuclear lamina mechanics |
| Cytoskeleton | Contractile springs/fibers | Active gel, actin polarity, myosin contractility |
| Adhesions | Discrete spring bonds to substrate | Molecular clutch attach/detach kinetics |
| Substrate | Flat elastic or rigid plane | Stiffness gradients, viscoelastic substrate, ECM fibers |

## Most Important Anchors

- Maxian, Mogilner, and Strychalski (2020) is the closest conceptual match because it includes active cortex, nucleus, ECM mechanics, cytoplasm/nucleoplasm flow, and push-pull versus rear-squeezing migration.
- Molecular clutch literature justifies modeling adhesions as dynamic force-transmitting bonds.
- Active gel literature justifies treating the actomyosin cytoskeleton/cortex as active, contractile, and overdamped rather than inertial.
- Nuclear mechanosensing/mechanics literature justifies making the nucleus mechanically distinct instead of only decorative.

