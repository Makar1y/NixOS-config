{ self, inputs, ... }: {

	flake.wrappers.niri = { pkgs, wlib, ... }: {
		imports = [ wlib.wrapperModules.niri ];
		settings = {
			input.keyboard.xkb.layout = "us,lt,ru";
			input.touchpad = {
				tap = _: { };
			};
			layout.gaps = 5;
			spawn-at-startup = [
				"noctalia-shell"
			];
			binds = import ./_binds.nix;
		};
	};

	flake.nixosModules.niri = { pkgs, lib, ... }: {
		programs.niri = {
			enable = true;
			package = self.packages.${pkgs.stdenv.hostPlatform.system}.niri;
		};
	};
}
