{
  inputs = {
    nixpkgs = {
      url = "github:NixOS/nixpkgs/nixos-unstable";
    };

    flake-parts = {
      url = "github:hercules-ci/flake-parts";
    };
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake {inherit inputs;} {
      # Import local override if it exists
      imports = [
        (
          if builtins.pathExists ./local.nix
          then ./local.nix
          else {}
        )
      ];

      # Sensible defaults
      systems = [
        "x86_64-linux"
        "i686-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      perSystem = {
        config,
        lib,
        pkgs,
        system,
        ...
      }: let
        node = pkgs.nodejs;
        python = pkgs.python311;
        nil = pkgs.nil;
        task = pkgs.go-task;
        coreutils = pkgs.coreutils;
        trunk = pkgs.trunk-io;
        poetry = pkgs.poetry;
        copier = pkgs.copier;
        openssl = pkgs.openssl;
        tini = pkgs.tini;
        su-exec = pkgs.su-exec;
      in {
        # Override pkgs argument
        _module.args.pkgs = import inputs.nixpkgs {
          inherit system;
          config = {
            # Allow packages with non-free licenses
            allowUnfree = true;
            # Allow packages with broken dependencies
            allowBroken = true;
            # Allow packages with unsupported system
            allowUnsupportedSystem = true;
          };
        };

        # Set which formatter should be used
        formatter = pkgs.alejandra;

        # Define multiple development shells for different purposes
        devShells = {
          default = pkgs.mkShell {
            name = "dev";

            packages = [
              node
              python
              nil
              task
              coreutils
              trunk
              poetry
              copier
            ];

            PYTHON_SITE_PACKAGES = "${python.sitePackages}";

            shellHook = ''
              export TMPDIR=/tmp
              export PRISMA_DB_URL="postgres://user:''${EMISHOWS__DATABASE__PASSWORD:-password}@''${EMISHOWS__DATABASE__HOST:-localhost}:''${EMISHOWS__DATABASE__PORT:-34000}/database"
              task install
              task generate-prisma
              . .venv/bin/activate
              export PYTHONPATH="''${VIRTUAL_ENV:?}/''${PYTHON_SITE_PACKAGES:?}:''${PYTHONPATH:-}"
            '';
          };

          package = pkgs.mkShell {
            name = "package";

            packages = [
              python
              task
              coreutils
              poetry
            ];

            PYTHON_SITE_PACKAGES = "${python.sitePackages}";

            shellHook = ''
              export TMPDIR=/tmp
              task install
              task generate-prisma
              . .venv/bin/activate
              export PYTHONPATH="''${VIRTUAL_ENV:?}/''${PYTHON_SITE_PACKAGES:?}:''${PYTHONPATH:-}"
            '';
          };

          runtime = pkgs.mkShell {
            name = "runtime";

            packages = [
              node
              python
              poetry
              openssl
              tini
              su-exec
            ];

            LD_LIBRARY_PATH = lib.makeLibraryPath [openssl];
            PYTHON_SITE_PACKAGES = "${python.sitePackages}";

            shellHook = ''
              export TMPDIR=/tmp
            '';
          };

          template = pkgs.mkShell {
            name = "template";

            packages = [
              task
              coreutils
              copier
            ];

            shellHook = ''
              export TMPDIR=/tmp
            '';
          };

          lint = pkgs.mkShell {
            name = "lint";

            packages = [
              node
              task
              coreutils
              trunk
            ];

            shellHook = ''
              export TMPDIR=/tmp
            '';
          };

          test = pkgs.mkShell {
            name = "test";

            packages = [
              node
              python
              task
              coreutils
              poetry
              openssl
            ];

            LD_LIBRARY_PATH = lib.makeLibraryPath [openssl];
            PYTHON_SITE_PACKAGES = "${python.sitePackages}";

            shellHook = ''
              export TMPDIR=/tmp
              task install
              task generate-prisma
              . .venv/bin/activate
              export PYTHONPATH="''${VIRTUAL_ENV:?}/''${PYTHON_SITE_PACKAGES:?}:''${PYTHONPATH:-}"
            '';
          };

          docs = pkgs.mkShell {
            name = "docs";

            packages = [
              node
              task
              coreutils
            ];

            shellHook = ''
              export TMPDIR=/tmp
            '';
          };
        };
      };
    };
}