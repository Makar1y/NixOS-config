{ self, ... }: {
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
					--prefix PATH : ${pkgs.niri}/bin \
					--prefix PATH : ${pkgs.opencode}/bin
				runHook postInstall
			'';
		};
	};

	flake.nixosModules.worklog = { pkgs, ... }: {
		systemd.user.services.worklog-tracker = {
			description = "Background activity tracker";
			wantedBy = [ "graphical-session.target" ];
			serviceConfig = {
				ExecStart =
					"${self.packages.${pkgs.stdenv.hostPlatform.system}.worklog}/bin/worklog track";
				Restart = "always";
			};
		};
		systemd.user.services.worklog-sync = {
			description = "Categorize and push activity to Clockify";
			serviceConfig.ExecStart =
				"${self.packages.${pkgs.stdenv.hostPlatform.system}.worklog}/bin/worklog sync";
		};
		systemd.user.timers.worklog-sync = {
			description = "Sync activity to Clockify every 3h";
			wantedBy = [ "timers.target" ];
			timerConfig = {
				OnBootSec = "10min";
				OnUnitActiveSec = "3h";
				Persistent = true;
			};
		};
	};
}