let
  pkgs = import <nixpkgs> {};
  pyPkgs = pkgs.python3Packages;
  buildPythonPackage = pkgs.python3Packages.buildPythonPackage;
  
  py-cord = pkgs.callPackage deps_nix/pycord.nix {inherit buildPythonPackage pkgs pyPkgs;};
  async_chain = pkgs.callPackage deps_nix/async_chain.nix {inherit buildPythonPackage pkgs pyPkgs;};
  
in
pkgs.mkShell {
  packages = with pkgs.python3Packages; [
    rich
    
    py-cord
    aiohttp
    aiofiles
    async_chain
    python-dotenv
    loguru
    prompt-toolkit
    rich
  ];
}