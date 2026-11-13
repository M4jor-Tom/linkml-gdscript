{
  description = "Development shell for linkml-gdscript";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.nixpkgs-godot-floor.url =
    "github:NixOS/nixpkgs/966d5ad75a4e79dc81edae64933f4900dca3a537";

  outputs =
    { nixpkgs, nixpkgs-godot-floor, ... }:
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
          floor = nixpkgs-godot-floor.legacyPackages.${system}.godot_4_5;
          mkDevShell = engine: expectedVersion: pkgs.mkShell {
            packages = [
              pkgs.uv
              pkgs.python314
              pkgs.python311 # oldest Python in nixpkgs; CI also covers 3.10
              pkgs.ruff # the ruff wheel installed by uv cannot run on NixOS
              pkgs.pre-commit
              engine
            ];
            # uv's downloaded interpreters cannot run on NixOS: use the ones above.
            UV_PYTHON_DOWNLOADS = "never";
            GODOT_EXPECTED_VERSION = expectedVersion;
          };
        in
        {
          default = mkDevShell pkgs.godot_4 "4.7.2.stable";
          godot-floor = mkDevShell floor "4.5.stable";
        }
      );
    };
}
