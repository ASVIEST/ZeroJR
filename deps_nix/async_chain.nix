{
  lib,
  pkgs,
  buildPythonPackage,
  pyPkgs,
}:
buildPythonPackage rec {
  pname = "async-chain";
  version = "0.1.2";
  pyproject = true;
  src = pkgs.fetchPypi {
    inherit pname version;
    hash = "sha256-wuNkj7Ws/oUMBRo4ru4TBCn9CkYmE1U0k/ESyVNd5mQ=";
  };
  dependencies = with pyPkgs; [
    # nativeBuildInputs pkgs.autoPatchelfHook
    poetry-core
    wheel
    setuptools
    atomicwrites
    attrs
    colorama
    importlib-metadata
    iniconfig
    packaging
    pluggy
    py
    toml
  ];
  pythonImportsCheck = [
    "async_chain"
  ];
  build-system = [
    pyPkgs.poetry-core
  ];
}
