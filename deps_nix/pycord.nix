{
  lib,
  pkgs,
  buildPythonPackage,
  pyPkgs,
}:
buildPythonPackage rec {
  pname = "py_cord";
  version = "2.6";
  pyproject = true;
  src = pkgs.fetchFromGitHub {
    owner = "Pycord-Development";
    repo = "pycord";
    rev = "refs/tags/v${version}";
    hash = "sha256-yj42zrvPYlPZmFuhiBIRE5BA7rutCEbOJopvBYofFPg=";
  };
  build-system = [ pyPkgs.setuptools ];
  dependencies = with pyPkgs; [
    setuptools
    setuptools-scm
    aiohttp
    # speedups
    # msgspec
    aiodns
    brotli
  ];
}