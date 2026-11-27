{ lib, stdenvNoCC }:

stdenvNoCC.mkDerivation {
  pname = "anon-check";
  version = lib.removeSuffix "\n" (builtins.readFile ../VERSION);

  src = lib.fileset.toSource {
    root = ../.;
    fileset = lib.fileset.unions [
      ../bin
      ../src
      ../tests
      ../eval
      ../Containerfile
      ../models.tsv
      ../pyproject.toml
      ../VERSION
    ];
  };

  dontBuild = true;

  installPhase = ''
    mkdir -p $out/share/anon-check $out/bin
    cp -r . $out/share/anon-check
    ln -s $out/share/anon-check/bin/anon-check $out/bin/anon-check
    ln -s $out/share/anon-check/bin/anon-check-build $out/bin/anon-check-build
  '';

  meta = {
    description = "Offline filter that reports or masks personal data in text on stdin";
    mainProgram = "anon-check";
  };
}
