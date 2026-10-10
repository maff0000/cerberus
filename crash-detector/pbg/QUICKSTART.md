# PBGv2 quick start

```text
COPY  →  BOOT  →  ASSIGN PROJECT LEAD  →  BUILD
```

## Two ways in

**Route A — you have an application already.** Copy PBG in, and the Project Lead discovers and
governs the current state. Follow the steps below.

**Route B — you designed the product with ChatGPT first.** Generate the PL handover before you
copy anything. See *Already designed the application with ChatGPT?* below.

## 1. Copy the framework into your project

```bash
cp -a /srv/pbgv2/dist/pbg  /srv/your-project/pbg
```

## 2. Copy the bootstrap adapter into the project root

```bash
# Claude Code
cp /srv/your-project/pbg/adapters/claude-code/CLAUDE.md  /srv/your-project/CLAUDE.md

# OpenCode or any other agent runtime
cp /srv/your-project/pbg/adapters/generic/AGENTS.md      /srv/your-project/AGENTS.md
```

## 3. Start your coding agent from the project root

```bash
cd /srv/your-project
```

## 4. Assign the role

```text
You are Project Lead.
```

## 5. Read the boot report

The Project Lead boots the framework itself and reports:

```text
PBG BOOT: GREEN | AMBER | BLOCKED

Project · PID · Blueprint · PBG version · Repository · Current SHA
Active work · Open decisions · Current risks · Next recommended action
```

## 6. Supply the PID if asked

A new project has no product constitution, so the Project Lead will return
`PID_DISCOVERY_REQUIRED` and start a structured conversation to build one. That is correct
behaviour, not an error. An existing codebase with no PID gets read-only discovery first — the
code tells you what *is*, only you can say what *should be*.

## 7. Approve the decisions that are yours

The Project Lead escalates by exception. Routine implementation choices are its own; anything
touching product direction, scope, major architecture, cost, risk, irreversible effect or the
security model comes to you with a recommendation and a default safe action.

---

## Already designed the application with ChatGPT?

1. Open `pbg/chatGPT-prompt.txt`.
2. Paste it into the same ChatGPT conversation where the product was designed.
3. Copy the generated Project Lead prompt.
4. Start Claude Code or OpenCode in the application directory.
5. Paste the Project Lead prompt.
6. The PL boots the local `pbg/` framework and begins from the supplied PID.

The generated prompt is a **handover artefact, not the PID**. It carries a proposed PID for you to
validate; once the PL commits `PID.md` and `BLUEPRINT.md`, those become canonical and the prompt is
only provenance. It also does not replace PBG — governance still comes from the local `pbg/`
directory.

---

## That is the whole setup

No global install. No Redis. No database. No service. No cloud account. No access to the PBGv2
repository after copying. The `pbg/` directory is self-contained and is now **your project's
pinned framework** — it cannot change underneath your work.

## Verify at any time

Run these **from your project root** — the directory that contains `pbg/`, not `pbg/` itself.

```bash
PYTHONPATH=pbg/tools python3 -B -m pbg.cli validate   # integrity of the pinned snapshot
PYTHONPATH=pbg/tools python3 -B -m pbg.cli status     # where the project is, and the next safe action
PYTHONPATH=pbg/tools python3 -B -m pbg.cli boot       # full Project Lead boot verdict
```

`validate` reports both roots, so you can see which tree each answer came from:

```
governed project root  /path/to/your-project
framework source root  /path/to/your-project/pbg
layout                 VENDORED
selected manifest      /path/to/your-project/pbg-manifest.yaml
selected instructions  /path/to/your-project/CLAUDE.md
```

**Your project root is the governed one.** `pbg/` holds the implementation; it is never the thing
being governed. If you vendor the framework somewhere the layout does not recognise — deeper than
`pbg/` or `governance/pbg/` — `validate` will refuse rather than guess, and tell you to say which
directory it governs:

```bash
PYTHONPATH=vendor/pbg/tools python3 -B -m pbg.cli --root . validate
```

`--root` names **your project**, never the framework directory.

## Two rules worth knowing on day one

**`pbg/` is read-only.** Your project's own truth lives outside it — `PID.md`, `BLUEPRINT.md`,
`governance/`. If you find a framework defect, record it, propose it upstream, and upgrade
deliberately. Do not patch the vendored copy; a silently patched framework is no longer a pinned
one.

**Project-local extensions go in `governance/pbg-extensions/`.** They may add controls, skills and
checks, and may strengthen policy. They cannot remove a mandatory control, weaken a non-waivable
one, or override role assignment.

## Upgrading

Copy a newer `dist/pbg` over the old one as an explicit, recorded action, then re-verify. Nothing
upgrades automatically — that is the point of pinning.
