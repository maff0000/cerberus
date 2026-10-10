# PBGv2 ROOT-OF-TRUST DECISION — two trust planes

**Recorded by:** PROJECT_LEAD seat, 2026-08-08, under Product Authority direction
**Authorised by:** PRODUCT_AUTHORITY ruling of 2026-08-08
**Status:** DOCTRINE. Declarative. It defines no schema, no control, no validator and no runtime.
**Occasioned by:** `FWK-OBS-019`, and by the shape shared with `FWK-OBS-007`, `014`, `015`, `017`.

---

## 1. The decision

PBGv2 has **two trust planes**, and they have until now been treated as one.

```
ROOT GOVERNANCE PLANE
    Establishes immutable doctrine, authority, and the narrowly bounded ability to repair
    governance machinery itself. TINY. RARELY USED.

NORMAL GOVERNED EXECUTION PLANE
    Uses that machinery to dispatch, bind, supervise and assure ordinary Engineer and
    Assurance seats. CARRIES ESSENTIALLY ALL WORK.
```

**Trying to make the second plane recursively establish its own root is what produced the repeated
circularities.** That is the conceptual repair.

## 2. What the five findings were actually saying

`FWK-OBS-007`, `014`, `015`, `017` and `019` share one shape: PBGv2 governing the creation of the
agents that govern it. Five instances of one shape is data, and it was tempting to read it as
*"internal self-dispatch is wrong"*.

**Product Authority ruled that reading incorrect.** The finding is narrower and more useful:

> **PBGv2 has been treating its root bootstrap mechanism as though it were ordinary governed workload
> dispatch.** That is the modelling mistake.

Internal self-dispatch is **RETAINED** for normal PBGv2 work. It is not the defect.

## 3. The boundary, stated plainly

> A dispatch system cannot be required to prove, using the repaired dispatch system, the legitimacy
> of the Engineer who is repairing that dispatch system.

This is not a failure of PBGv2. It is its **root-of-trust boundary**, and it has now been located
empirically rather than argued.

```
NORMAL GOVERNED WORK      PBGv2 dispatches and binds its own Engineer and Assurance seats.

FRAMEWORK ROOT REPAIR     Repairs the mechanism that makes NORMAL GOVERNED WORK possible.
                          It cannot recursively depend on the broken mechanism being repaired.
```

These become **two explicit classes**, not one class plus repeated exceptions.

## 4. The trust chain

```
PRODUCT AUTHORITY
      ↓
FRAMEWORK_BOOTSTRAP_REPAIR authority
      ↓
named bootstrap Engineer
      ↓
repair of ordinary dispatch machinery
      ↓
FRESH ORDINARY CONSUMER proves the repaired machinery
```

**That is not circular.** Product Authority is already the root that authorises adoption,
commissioning and authority creation. The decision recorded here is the acknowledgement that
**the root cannot itself be manufactured by the downstream mechanism it governs.**

## 5. What this is NOT

- **NOT an exception.** The word is retired for this purpose. `binding_status: NON_BINDING` +
  `bootstrap_exception: true` + `ordinal: twelfth` is a **finished model**.
- **NOT a dispatch bypass.** A bootstrap seat has **LESS** freedom than a normal seat, not more.
- **NOT a satisfier of normal binding.** `FRAMEWORK_BOOTSTRAP_REPAIR` does **not** satisfy
  `NORMAL_DISPATCH_BINDING`. Two distinct lawful provenance types. This is what prevents
  `FWK-OBS-014` reappearing under a more respectable name.
- **NOT a licence for the PROJECT_LEAD to implement.** The PL may author declarative contracts under
  Product Authority direction. Validator and runtime behaviour remain **Engineer work**.

## 6. Roles, unchanged

```
Product Authority / PL   doctrine, contracts, authority
Engineer                 implementation
Assurance                independent proof
```

## 7. The eleven historical records

The eleven ungated spawn records are **PRESERVED and NON_BINDING, permanently**. Nothing in this
decision reinterprets them, and a future working `FRAMEWORK_BOOTSTRAP_REPAIR` must not either. The
migration proof PBGv2 owes remains:

```
old ungated records    PRESERVED · NON_BINDING
new records            BINDING · DISPATCH-PROVEN
```

## 8. Ordering this decision imposes

```
A  record the root-of-trust decision                        ← this document
B  freeze the temporal / base-bearing contract
C  freeze a minimal FRAMEWORK_BOOTSTRAP_REPAIR contract
D  create the narrow FWK-OBS-019 implementation authority
E  bootstrap Engineer under that contract
F  deliver candidate
G  ORDINARY consumer proves normal binding
H  fresh Assurance
```

**`G` is the closure proof for `FWK-OBS-019`.** The bootstrap candidate cannot prove its own success.
If ordinary consumption fails, the bootstrap repair fails.
