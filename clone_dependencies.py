import os
import subprocess
from pathlib import Path

base = Path(__file__).parent.resolve() / "deps/"

APP_SOLANA_URL = "git@github.com:LedgerHQ/app-solana.git"
APP_SOLANA_CLONE_DIR = base / "app-solana/"
APP_BOILERPLATE_URL = "git@github.com:LedgerHQ/app-boilerplate.git"
APP_BOILERPLATE_DIR = base / "app-boilerplate/"
LEDGER_SDK_URL = "git@github.com:LedgerHQ/ledger-secure-sdk.git"
LEDGER_SDK_CLONE_DIR = base / "ledger-secure-sdk/"

APP_BOILERPLATE_RUST_URL = "git@github.com:LedgerHQ/app-boilerplate-rust.git"
APP_BOILERPLATE_RUST_DIR = base / "app-boilerplate-rust/"
LEDGER_RUST_SDK_URL = "git@github.com:LedgerHQ/ledger-device-rust-sdk.git"
LEDGER_RUST_SDK_CLONE_DIR = base / "ledger-device-rust-sdk/"

def run_cmd(cmd: str,
            cwd: Path = Path('.'),
            print_output: bool = False,
            no_throw: bool = False) -> str:

    print(f"[run_cmd] Running: '{cmd}'' inside '{cwd}'")

    ret = subprocess.run(cmd,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         universal_newlines=True,
                         cwd=cwd)
    if no_throw is False and ret.returncode:
        print(f"[run_cmd] Error {ret.returncode} raised while running cmd: {cmd}")
        print("[run_cmd] Output was:")
        print(ret.stdout)
        raise ValueError()

    if print_output:
        print(f"[run_cmd] Output:\n{ret.stdout}")

    return ret.stdout.strip()

def clone_or_pull(repo_url: str, clone_dir: str, branch):
    # Only needed when cloning / pulling, not when building.
    # By putting the import here we allow the script to be imported inside the docker image
    from git import Repo
    git_dir = os.path.join(clone_dir, ".git")
    if not os.path.exists(git_dir):
        run_cmd(f"rm -rf {clone_dir}")
        print(f"Cloning into {clone_dir}")
        Repo.clone_from(repo_url, clone_dir, recursive=True)
    else:
        print(f"Pulling latest changes in {clone_dir}")
        repo = Repo(clone_dir)
        origin = repo.remotes.origin
        origin.fetch()
        repo.git.reset('--hard', f'origin/{branch}')

        # Update submodules
        print(f"Updating submodules in {clone_dir}")
        run_cmd("git submodule sync", cwd=Path(clone_dir))
        run_cmd("git submodule update --init --recursive", cwd=Path(clone_dir))

clone_or_pull(APP_SOLANA_URL, APP_SOLANA_CLONE_DIR, "develop")
clone_or_pull(APP_BOILERPLATE_URL, APP_BOILERPLATE_DIR, "master")
clone_or_pull(LEDGER_SDK_URL, LEDGER_SDK_CLONE_DIR, "master")
clone_or_pull(APP_BOILERPLATE_RUST_URL, APP_BOILERPLATE_RUST_DIR, "main")
clone_or_pull(LEDGER_RUST_SDK_URL, LEDGER_RUST_SDK_CLONE_DIR, "master")
