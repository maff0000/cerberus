"""Project-owned hook commissioning (independent Assurance finding F23).

THE FINDING. `ENFORCEMENT_TRUTH` declares "project-owned pre-commit hook, when installed →
ENFORCED". The statement was honest; its precondition was unmet. On the repository where authority
records are actually written, `core.hooksPath` was unset and `.git/hooks/pre-commit` absent, so
prevention was nil and rested entirely on the supported writer being used voluntarily. The hook was
proved installable and effective on a clone; it was simply never commissioned where it mattered, and
nothing reported that gap.

WHAT THIS IS. A bounded, supported, reversible mechanism — install, status, uninstall — using
REPOSITORY-LOCAL configuration only. It writes `core.hooksPath` into the repository it is pointed at
and nothing else. Nothing is written to `~/.gitconfig`, to `--global`, or to `--system`; a
governance control that requires editing the machine is not portable, and PBG ships to other
machines.

WHAT THIS IS NOT. Universal enforcement. `git commit --no-verify` bypasses any pre-commit hook, and
so does writing objects with plumbing. That limit is REPORTED rather than hidden, because
`ENFORCEMENT_TRUTH`'s existing honesty is the standard to preserve — a control that overstates
itself is worse than one that does not exist, since people stop checking.

THE WORKTREE HAZARD, and why it is a refusal rather than a warning. In a LINKED worktree,
`git config --local` does not write to that worktree. Unless `extensions.worktreeConfig` is enabled
it writes to the SHARED config in the common git directory, so commissioning one worktree silently
reconfigures the main checkout and every sibling worktree at once. That is a mutation of a
repository the operator did not name. `install()` detects the condition and REFUSES; it does not
warn and proceed.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

#: Where the project's own hooks live, tried in order. The second is what a CONSUMING project has:
#: the framework is vendored as a `pbg/` snapshot, so its hooks sit one level in.
HOOK_DIRECTORIES = ("tools/hooks", "pbg/tools/hooks")

#: The config key. The ONLY key this module ever writes.
HOOKS_PATH_KEY = "core.hooksPath"

#: Where a pre-existing hooksPath is remembered so uninstall can put it back. Repository-local,
#: namespaced to PBG so it cannot collide with anything the project owns.
PREVIOUS_KEY = "pbg.previousHooksPath"

INSTALLED = "INSTALLED"
NOT_INSTALLED = "NOT_INSTALLED"
FOREIGN = "FOREIGN"
REFUSED = "REFUSED"
NOT_A_REPOSITORY = "NOT_A_REPOSITORY"

#: Restated here so the commissioning surface cannot drift from the framework's own statement.
BYPASSES = (
    "git commit --no-verify bypasses this hook, as it bypasses every pre-commit hook",
    "writing objects with git plumbing bypasses the commit path entirely",
    "a hook is a gate on the supported path, not a property of the repository format",
)


@dataclass
class HookState:
    status: str
    detail: str
    hooks_path: str | None = None
    resolved_hook: Path | None = None
    previous: str | None = None
    global_hooks_path: str | None = None
    system_hooks_path: str | None = None
    shared_config: bool = False
    findings: list[str] = field(default_factory=list)

    @property
    def commissioned(self) -> bool:
        return self.status == INSTALLED

    def render(self) -> str:
        lines = [
            f"PBG HOOK COMMISSIONING: {self.status}",
            "",
            f"  {self.detail}",
            "",
            f"  {HOOKS_PATH_KEY} (local)   {self.hooks_path or '<unset>'}",
            f"  {HOOKS_PATH_KEY} (global)  {self.global_hooks_path or '<unset>'}",
            f"  {HOOKS_PATH_KEY} (system)  {self.system_hooks_path or '<unset>'}",
            f"  hook file                  {self.resolved_hook or '<none>'}",
        ]
        if self.previous:
            lines.append(f"  saved previous hooksPath   {self.previous}")
        if self.findings:
            lines += ["", "  findings:"] + [f"    - {f}" for f in self.findings]
        lines += ["", "  What this does NOT prevent:"] + [f"    - {b}" for b in BYPASSES]
        return "\n".join(lines)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def _config_get(root: Path, scope: str, key: str) -> str | None:
    result = _git(root, "config", scope, "--get", key)
    return result.stdout.strip() or None if result.returncode == 0 else None


def toplevel(root: Path) -> Path | None:
    result = _git(root, "rev-parse", "--show-toplevel")
    return Path(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip() else None


def writes_to_shared_config(root: Path) -> bool:
    """True when `git config --local` here would also reconfigure other worktrees.

    A linked worktree's `--local` scope IS the shared config unless `extensions.worktreeConfig` is
    on. Determined by observation rather than assumed: git-dir and git-common-dir differ only in a
    linked worktree.
    """
    git_dir = _git(root, "rev-parse", "--absolute-git-dir").stdout.strip()
    common = _git(root, "rev-parse", "--git-common-dir").stdout.strip()
    if not git_dir or not common:
        return False
    # `--git-common-dir` answers RELATIVE to the working directory in a normal checkout and
    # absolute in a linked worktree. Comparing the two without anchoring the relative one resolves
    # it against the process's cwd, which made every ordinary repository look linked.
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = Path(root) / common_path
    linked = Path(git_dir).resolve() != common_path.resolve()
    if not linked:
        return False
    return _config_get(root, "--local", "extensions.worktreeConfig") not in ("true", "1")


def find_hook_directory(project_root: Path) -> tuple[str, Path] | None:
    """The project's own hooks directory, PROJECT_ROOT-relative. Never an absolute host path.

    Relative on purpose: `core.hooksPath` stored as `tools/hooks` keeps working after the project is
    moved, which is most of what "works after relocation" means.
    """
    for rel in HOOK_DIRECTORIES:
        candidate = project_root / rel
        if (candidate / "pre-commit").is_file():
            return rel, candidate
    return None


def status(project_root: Path) -> HookState:
    """Report the commissioning state. Reads only — never writes, never installs as a side effect."""
    root = Path(project_root)
    top = toplevel(root)
    if top is None:
        return HookState(NOT_A_REPOSITORY, f"{root} is not inside a Git repository")

    local = _config_get(root, "--local", HOOKS_PATH_KEY)
    state = HookState(
        NOT_INSTALLED,
        "no project-owned hook is commissioned on this repository",
        hooks_path=local,
        previous=_config_get(root, "--local", PREVIOUS_KEY),
        global_hooks_path=_config_get(root, "--global", HOOKS_PATH_KEY),
        system_hooks_path=_config_get(root, "--system", HOOKS_PATH_KEY),
        shared_config=writes_to_shared_config(root),
    )

    found = find_hook_directory(top)
    if state.shared_config:
        state.findings.append(
            "this is a LINKED WORKTREE and extensions.worktreeConfig is not enabled, so a "
            "repository-local write here lands in the shared config and would reconfigure the "
            "main checkout and every sibling worktree")

    if local is None:
        if found:
            state.detail = ("not commissioned; the project's hooks are present at "
                            f"{found[0]} and can be installed")
        else:
            state.detail = "not commissioned, and this project ships no pbg hooks directory"
        return state

    resolved = (top / local) if not Path(local).is_absolute() else Path(local)
    state.resolved_hook = resolved / "pre-commit"
    ours = found is not None and resolved.resolve() == found[1].resolve()

    if ours and state.resolved_hook.is_file():
        state.status = INSTALLED
        state.detail = f"project-owned hook commissioned via {HOOKS_PATH_KEY}={local}"
    elif ours:
        state.status = NOT_INSTALLED
        state.detail = (f"{HOOKS_PATH_KEY}={local} points at the project's hooks directory, but "
                        "pre-commit is not present there")
    else:
        state.status = FOREIGN
        state.detail = (f"{HOOKS_PATH_KEY}={local} is set to something this project does not own; "
                        "PBG will not overwrite it without an explicit re-commission")
    if Path(local).is_absolute():
        state.findings.append(
            f"{HOOKS_PATH_KEY} is an ABSOLUTE path; it will not survive relocation of this project")
    return state


def install(project_root: Path, *, force: bool = False) -> HookState:
    """Commission the project's own hook. Idempotent, repository-local, reversible."""
    root = Path(project_root)
    top = toplevel(root)
    if top is None:
        return HookState(NOT_A_REPOSITORY, f"{root} is not inside a Git repository")

    # PROJECT_ROOT validation. Commissioning the wrong repository is worse than not commissioning:
    # it writes configuration into a tree the operator did not name.
    if top.resolve() != root.resolve():
        return HookState(
            REFUSED,
            f"{root} is not the repository top level ({top}). Point commissioning at PROJECT_ROOT, "
            "so it is unambiguous which repository is being configured.")

    found = find_hook_directory(top)
    if found is None:
        return HookState(
            REFUSED,
            f"no pbg hooks directory with a pre-commit under {top} "
            f"(looked for {', '.join(HOOK_DIRECTORIES)}); there is nothing to commission")
    rel, hook_dir = found

    current = status(top)

    if current.shared_config:
        # The refusal AUTH-0012 anticipated. Enabling extensions.worktreeConfig would fix it, but
        # that is a different config key and a wider change than commissioning a hook — so this
        # reports the condition and stops rather than quietly widening its own scope.
        state = HookState(
            REFUSED,
            "this is a linked worktree without extensions.worktreeConfig, so a repository-local "
            "write would land in the SHARED config and silently reconfigure the main checkout and "
            "every sibling worktree. Refusing: commissioning one worktree must not reconfigure "
            "repositories nobody named.",
            hooks_path=current.hooks_path, shared_config=True)
        state.findings = list(current.findings)
        return state

    if current.status == INSTALLED and not force:
        current.detail = f"already commissioned via {HOOKS_PATH_KEY}={current.hooks_path}; no change"
        return current

    if current.status == FOREIGN and not force:
        return HookState(
            REFUSED,
            f"{HOOKS_PATH_KEY} is already set to {current.hooks_path!r}, which this project does "
            "not own. Refusing to overwrite another mechanism's configuration; re-run with force "
            "to take it over, and the previous value will be saved.",
            hooks_path=current.hooks_path)

    # Remember what was there, so uninstall can put it back. Only ever recorded when there IS a
    # prior value and we have not already saved one.
    if current.hooks_path and not current.previous:
        _git(top, "config", "--local", PREVIOUS_KEY, current.hooks_path)

    result = _git(top, "config", "--local", HOOKS_PATH_KEY, rel)
    if result.returncode != 0:
        return HookState(REFUSED, f"git refused the configuration write: {result.stderr.strip()}")

    hook = hook_dir / "pre-commit"
    if not hook.stat().st_mode & 0o111:
        hook.chmod(hook.stat().st_mode | 0o111)

    final = status(top)
    final.detail = f"commissioned: {HOOKS_PATH_KEY}={rel} (repository-local only)"
    return final


def uninstall(project_root: Path) -> HookState:
    """Decommission, restoring any configuration that was there before PBG took it over."""
    root = Path(project_root)
    top = toplevel(root)
    if top is None:
        return HookState(NOT_A_REPOSITORY, f"{root} is not inside a Git repository")

    before = status(top)
    if before.shared_config:
        return HookState(
            REFUSED,
            "this is a linked worktree without extensions.worktreeConfig; unsetting here would "
            "alter the shared config for every worktree. Refusing.",
            hooks_path=before.hooks_path, shared_config=True)

    previous = before.previous
    if previous:
        _git(top, "config", "--local", HOOKS_PATH_KEY, previous)
        _git(top, "config", "--local", "--unset", PREVIOUS_KEY)
        final = status(top)
        final.detail = f"decommissioned; restored the previous {HOOKS_PATH_KEY}={previous}"
        return final

    _git(top, "config", "--local", "--unset", HOOKS_PATH_KEY)
    final = status(top)
    final.detail = ("decommissioned; there was no previous value, so the key is unset and the "
                    "repository is back to Git's default hooks directory")
    return final
