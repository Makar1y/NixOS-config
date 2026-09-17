{ ... }: {
	perSystem = { pkgs, ... }: {
		packages.monitorctl = pkgs.stdenv.mkDerivation {
			pname = "monitorctl";
			version = "0.1.0";
			src = ./monitorctl.py;
			dontUnpack = true;
			nativeBuildInputs = [ pkgs.makeWrapper ];
			buildInputs = [ pkgs.python3 ];
			installPhase = ''
				runHook preInstall
				mkdir -p $out/bin
				cp $src $out/bin/monitorctl
				chmod +x $out/bin/monitorctl
				patchShebangs $out/bin/monitorctl
				wrapProgram $out/bin/monitorctl \
					--prefix PATH : ${pkgs.niri}/bin \
					--prefix PATH : ${pkgs.yad}/bin
				runHook postInstall
			'';
		};
	};
}