{ ... }: {
	perSystem = { pkgs, ... }: {
		packages.worklog = pkgs.stdenv.mkDerivation {
			pname = "worklog";
			version = "0.1.0";
			src = ./worklog.py;
			dontUnpack = true;
			nativeBuildInputs = [ pkgs.makeWrapper ];
			buildInputs = [ pkgs.python3 ];
			installPhase = ''
				runHook preInstall
				mkdir -p $out/bin
				cp $src $out/bin/worklog
				chmod +x $out/bin/worklog
				patchShebangs $out/bin/worklog
				wrapProgram $out/bin/worklog \
					--prefix PATH : ${pkgs.niri}/bin
				runHook postInstall
			'';
		};
	};
}