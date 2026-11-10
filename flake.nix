{
  description = "Development shell for linkml-gdscript";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
    in
    {
      # Dev shell only: the package itself is built and locked by uv (uv.lock).
      devShells = nixpkgs.lib.genAttrs systems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.uv
              pkgs.python314
              pkgs.python311 # oldest Python in nixpkgs; CI also covers 3.10
              pkgs.ruff # the ruff wheel installed by uv cannot run on NixOS
              pkgs.pre-commit
              pkgs.godot_4 # godot4 --headless --check-only --script <file.gd>
            ];
            # uv's downloaded interpreters cannot run on NixOS: use the ones above.
            UV_PYTHON_DOWNLOADS = "never";
          };
        }
      );
    };
}
